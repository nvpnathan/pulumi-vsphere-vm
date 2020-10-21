__author__ = 'nvpnathan'

import pulumi
import pulumi_vsphere as vsphere

## Data Collection Parameters
datacenter  = 'pl-dc'
vmrp        = 'pl-terraform-vms'
vm_template = 'packer-ubuntu-2004-2020-10-19T1603138176'

## VM Parameters
vm_params = {
    'name':'vlab-pihole',
    'folder':'pl-packer-vms',
    'vcpu':'2',
    'mem':'2048',
    'disk_datastore':'nfs-01',
    'data_datastore':'nfs-01',
    'disk_size':'32',
    'data_size':'25',
    'linked_clone':True,
}

## VM IP Parameters
vm_net_params = {
    'domain':'vballin.com',
    'dns':'192.168.64.60',
    'hostname':'vlab-pihole',
    'ipv4':'192.168.64.44',
    'prefix_length':'24',
    'gateway':'192.168.64.1',
    'portgroup':'pl-vlab-mgmt',
}

## Data Collection
dc = vsphere.get_datacenter(name=datacenter)
respool = vsphere.get_resource_pool(datacenter_id=dc.id, name=vmrp)
template = vsphere.get_virtual_machine(datacenter_id=dc.id, name=vm_template)
disk_ds = vsphere.get_datastore(datacenter_id=dc.id, name=vm_params['disk_datastore'])
data_ds = vsphere.get_datastore(datacenter_id=dc.id, name=vm_params['data_datastore'])
pg = vsphere.get_network(datacenter_id=dc.id, name=vm_net_params['portgroup'])

## Create Data Disk
pd_disk = vsphere.VirtualDisk(vm_params['name'] + '-pd',
    datacenter=datacenter,
    datastore=vm_params['data_datastore'],
    size=vm_params['data_size'],
    type="thin",
    vmdk_path='data_vols/' + vm_params['name'] + '-pd.vmdk',
    opts=pulumi.ResourceOptions(protect=True),
)

## Create VM
vm = vsphere.VirtualMachine(resource_pool_id=respool.id, guest_id='ubuntu64Guest',
    resource_name=vm_params['name'], name=vm_params['name'], 
    num_cpus=vm_params['vcpu'],memory=vm_params['mem'], datastore_id=disk_ds.id,
    network_interfaces=[{'networkId':pg.id}],
    disks=[
        {'label':vm_params['name']+'.vmdk','size':vm_params['disk_size']},
        {'label':vm_params['name']+'pd.vmdk','size':vm_params['data_size'], 
        'path':pd_disk.vmdk_path,'unitNumber':1, 'datastore_id':data_ds.id,
        'diskMode':'independent_persistent'}
    ],
    clone={'templateUuid':template.id, 'linkedClone':vm_params['linked_clone'],
        'customize':{
            'linuxOptions':{
                'domain':vm_net_params['domain'],
                'hostName':vm_net_params['hostname'],
            },
            'dnsServerLists':[vm_net_params['dns']],
            'dnsSuffixLists':[vm_net_params['domain']],
            'ipv4Gateway':vm_net_params['gateway'],
            'network_interfaces':[{
                'ipv4_address':vm_net_params['ipv4'],
                'ipv4Netmask':vm_net_params['prefix_length'],
                'dnsServerLists':[vm_net_params['dns']]
            }]
        }
    }
)

## Outputs
pulumi.export('VM IP Address', vm.guest_ip_addresses)
pulumi.export('Hostname', vm.clone['customize']['linuxOptions']['hostName'])