#!/bin/expect -f
# ./passwordless_ssh.sh node username pass
spawn cortx_setup cluster create [lindex $argv 0] [lindex $argv 1] [lindex $argv 2] --name cortx_cluster --site_count 1 --storageset_count 1 --virtual_host [lindex $argv 4] --target_build [lindex $argv 5] 
set timeout 1200
expect {
    timeout {
        puts "Connection timed out"
        exit 1
    }
    
    -re "Enter root user password for.*" {
        send -- "[lindex $argv 3]\r"
        exp_continue
    }

    "assword:" {
        send -- "[lindex $argv 3]\r"
        exp_continue
    }
}
