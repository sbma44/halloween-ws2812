# Halloween Lights!

Hi Marc. Here's a bare-bones environment for making blinky lights. If you have time and feel inspired, I think this could be adapted into something cool!

There are two parts:
- a NodeMCU project written in Lua that is designed to do nothing but join a wifi network and expose a live interpreter on port 2323
- a Python script that scans for hosts with the correct open port and shows how to send code to them

## NodeMCU
You can find the project docs [here](https://nodemcu.readthedocs.io/en/master/en). The most important modules for us are the [ws2812](https://nodemcu.readthedocs.io/en/master/en/modules/ws2812/) and [tmr](https://nodemcu.readthedocs.io/en/master/en/modules/tmr/) modules. Give them both a quick read. Lua is a garbage language (1-indexed arrays?! gtfo) but the nodemcu environment's dependence on callbacks will seem familiar to any Node.js developer. There are a few gotchas, though:
- It's a very memory-constrained device. Lua does garbage collection, but be careful about memory leaks.
- The firmware that's on there right now can't do floating point, just ints. We can change that if need be.
- Everything runs on one thread, like Javascript. Unlike typical Javascript, that thread is also managing your wifi stack's lowest levels. So keeping the chip busy for too long can screw up networking. This probably isn't something you will need to worry about.

NodeMCU exposes an interactive Lua prompt on its serial port. When connected to your computer, you can get to it with `screen /dev/ttyUSB0 115200` (replace the tty with whatever your system calls it -- just look for the new entry in `/dev/tty*` upon plugging the chip in). Hitting the chip's reset button should display some boilerplate.

NodeMCU also has a filesystem, which calls `init.lua` at boot. This file should be left alone -- a badly-formed init.lua can brick your device, forcing reflashing (not a huge deal, but still). In this case, the file:
- loads `credentials.lua`, which contains a list of SSIDs and passwords
- scans for 802.11b(?) wifi networks and tries to connect to any it recognizes from the credentials file
- upon success, runs `application.lua`, which sets up a server on port 2323 that, upon connection, redirects serial i/o (which is connected to the lua interpreter) to the network socket and prints out the chip's unique ID to the client

The _right_ way to do NodeMCU development is using a tool like [nodemcu-uploader](https://github.com/kmpm/nodemcu-uploader) to upload your custom-built `application.lua` (stretch goal: if you get this working and download the credentials file you can steal my home wifi password). But I think it'll be simpler to simply blast new Lua code across the network. This is particularly true given that our goal is to have multiple devices. Better to have one machine that can connect to and update all of them, rather than needing to flash each one every time you update the software. Which brings us to:

## Python
The Python file is dead-simple, except for requiring Python 3. It runs a parallel scan of hosts on `192.168.1.*` (we should change that?) looking for port 2323. It collects the unique IDs available on that port and makes a list of the hosts that are up by IP.

And it exposes a convenience function for sending Lua code to a given chip ID (my thinking is that these will remain stably correlated to a place in the room, while IPs might change). Here it just sets a variable to prove everything works -- you can confirm by using the `screen` invocation listed above and doing a `print(PROOF_OF_LIFE)`. In a properly working system we will instead presumably send across Lua code that runs `ws2812.init()` etc.

## gotchas
- You cannot redefine functions in Lua as far as I can tell. `node.restart()` will reboot the system but it'll have to go through wifi rigamarole again. Anonymous functions are fine though, and of course variables can be reassigned, so I suspect something like the following will make sense:
```lua
step_1 = function()
  -- do some awesome ws2812 shit
  tmr.create():alarm(200, tmr.ALARM_SINGLE, step_2)
end

step_2 = function()
  -- yet more awesome shit
  tmr.create():alarm(200, tmr.ALARM_SINGLE, step_1)
end

step_1()
```
- I have not tested the above even a little
- You can always go the application.lua route!
- ok here's the big one: **DO NOT PLUG THE WEMOS INTO YOUR COMPUTER AND THE BIG LIGHT STRAND SIMULTANEOUSLY, _EVEN_ IF THE BIG STRANGE IS BEING POWERED BY THE STANDALONE POWER SUPPLY**. It's fine for the Wemos to be connected to the big strand, powered by the standalone power supply; and it's fine for the Wemos to be connected to your computer and nothing else; and it's fine for the Wemos to be connected to the short test strand and your computer. But big strand + computer = bad news. This is because your USB bus's voltage regulator is not designed to know that it's sharing its duties, and its target voltage might be slightly higher than the standalone power supply. If so, it will try to power the entire string of lights itself, which -- if enough of them are turned on -- can be several amps worth of current. In practice, I've never blown out an Apple USB port -- their voltage regulators are high quality, isolated from the rest of the system with thermal shutoff circuits. Amazingly, OS X will even give you a software prompt about it. Still, this is not good for your computer and will definitely not work. One of the nice things about the setup I have supplied you is that you can get into the NodeMCU interpreter over telnet (eg `telnet 192.168.1.123 2323`) so you can always try that first, if the thing is getting an IP. You should only need to connect to it by USB if the wifi connection stuff is busted or you want to mess with the NodeMCU filesystem.
