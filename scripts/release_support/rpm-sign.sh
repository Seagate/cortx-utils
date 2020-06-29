#!/usr/bin/expect -d

set PASSPHRASE [lindex $argv 0]
set RPM [lindex $argv 1]

spawn rpm --addsign {*}${RPM}
expect -exact "Enter pass phrase: "
send -- "${PASSPHRASE}\r"
expect eof
