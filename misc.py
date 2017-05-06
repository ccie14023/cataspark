import pexpect

def bgp_updown(updown, neighbor_ip, asn, device_ip, username, password):

	command = "{} neighbor {} shutdown"
	if updown == "up":
		command = command.format("no", neighbor_ip)
	elif updown == "down":
		command = command.format("",neighbor_ip)

	p=pexpect.spawn('ssh {}@{}'.format(username,device_ip))

	p.expect('word:')
	p.sendline(password)

	p.expect('#')
	p.sendline('conf t')

	p.expect('#')
	p.sendline('router bgp {}'.format(asn))

	p.expect('#')
	p.sendline(command)

	p.expect("#")
	p.sendline("end")



