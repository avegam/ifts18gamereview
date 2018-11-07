# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-16.04-i386"
  config.vm.network "forwarded_port", guest: 8000, host: 8000, host_ip: "127.0.0.1"
  config.vm.network "forwarded_port", guest: 8080, host: 8080, host_ip: "127.0.0.1"
  config.vm.network "forwarded_port", guest: 5000, host: 5000, host_ip: "127.0.0.1"

  # Work around disconnected virtual network cable.
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--cableconnected1", "on"]
    vb.name = "vir2"
  end

  config.vm.provision "shell", inline: <<-SHELL
    apt-get -qqy update
    apt-get -qqy upgrade
    apt-get -qqy install make zip unzip

    apt-get -qqy install python3 python3-pip
    pip3 install --upgrade pip
    pip3 install flask 
    pip3 install sqlalchemy flask-sqlalchemy psycopg2 bleach

    apt-get -qqy install python python-pip
    pip2 install --upgrade pip
    pip2 install flask
    pip2 install sqlalchemy flask-sqlalchemy psycopg2 bleach

    echo "Done installing your virtual machine!"
  SHELL
end
