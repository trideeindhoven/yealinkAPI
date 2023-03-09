#!/usr/bin/python3

from RPS import RPS
import config

rps = RPS(accessKeyID=config.accessKeyID, accessKeySecret=config.accessKeySecret)
print( rps.getServerList() )

print( rps.getServerDetails(id="xyz") )

print( rps.serverExists(name="PerfectvoIP"))
print( rps.serverExists(name="PerfectVoIP2"))

