Vagrant.configure("2") do |config|
    config.vm.box = "nntest"
    config.vm.box_url = "../../projects/nntest.box"
    config.vm.synced_folder "../../code", "/code"
    config.vm.define "master" do |cfg|
        cfg.vm.provision "shell", path: 'vm/master.sh'
        cfg.vm.network "public_network", :bridge => "br0"
    end
    @num_workers@.times do |i|
        config.vm.define "worker#{i}" do |cfg|
            cfg.vm.provision "shell", path: 'vm/worker.sh', args: "worker#{i} #{ENV['MASTER_IP']}"
            cfg.vm.network "public_network", :bridge => "@bridge@"
        end
    end
end
