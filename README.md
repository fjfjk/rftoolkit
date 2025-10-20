!!! WARNING: use this ONLY in isolated environments ONLY on YOUR owned property, seriously - you can get in legal trouble real fast.

Now that we got rid of all the whinies - "What even is this?"
- This is my RFToolkit, made for HackRF One SDR, currently in development, but all the features added right now work just fine
"What will be added?"
- Great question - Just added a "Protocols" tab, for now with just ADS-B protocol scan (BETA, please write any issues, i cant test it bc there are no planes flying over ukraine at the moment)
"Will it work with rtlsdr/bladesdr/whateversdr?"
- No, currently im making it only work with HackRF One, simply because its the only SDR i have, and im not posting untested code to public use(shoutout to yall kernel source posters)

Usage: First - run the setup.py to see if you have the needed stuff installed, then - rftoolkit.py, navigate from there using numbers and Enter's

About tabs:
1. RF_Replay - does exactly what it sounds like: record a signal, store it and replay when needed
2. GPS_Spoof - allows to spoof GPS signal on devices nearby using ephemeris satellite data file from NASA site(publicly available)
3. RF_Jamming - literally a jammer that allows you to either block one frequency, or sweep a wide range of frequencies(jamming by max available bandwidth and then making a step by that same bandwidth, or randomly, i made both) NOTE: jamming wide range of frequencies using sweeping/random method is not as effective, simply because we cant cover much with just one device
4. Protocols - for now contains just 1 option - ADS-B protocol scan, NEEDS TESTING(by others), i will add other stuff to it
5. Samples/Scripts (Portapack/FZ) - menu for using pre-recorded samples or activating interesting scripts(that im going to re-write for proper use) taken from different portapack and flipper zero firmwares

Bug reports:
I dont expect this thing to work for everyone and everywhere, i try to test all functions i add before pushing commits to github
BUT, i cant test some features myself(like ADS-B, because i dont have planes flying here)
PLEASE - submit ANY issues, and i mean ANY issues to here, i will answer to anything if you are not rage baiting and need help, this will really help the project

TODO:

- its so ugly...
- Actually make the Samples/Scripts tab functional
- Add more stuff to Protocols tab/fix ads-b if it doesnt work
- Remove all swears from code comments if i want to present this as a college coding project(the reason why im making this in python, lol)
