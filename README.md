# Network scripts
A collection of network scripts, mostly written in python. Used to retrieve and send 
information to network devices (mainly cisco).

## Scripts
### ISE scripts
A bunch of these scripts are related to Cisco ISE. They are used to collect MAC address 
from multiple devices to generate csv files which can be imported into ISE.
The order I use them in for extracting MAC addresses:
1. ise\_initial.py
  * To generate the initial files
2. ise\_mac\_extract.py (also as a cronjob)
  * To extract the MAC addresses from one or multiple switches
3. ise\_l2\_only\_mac.py 
  * is the same for l2 only vlans for which information can't be extract from the arp table
4. ise\_gen\_config.py
  * is used to generate the configuration based on the live configuration
  * It wil use the initial files to locate which vlans and ports to adjust and which to skip.
5. ise\_gen\_nad\_csv.py
  * can be used to generate the NAD's to be imported into Cisco ISE

### SW(itches) scripts
These scripts are mainly used to retrieve information from the devices. Like:
* l2 only vlans
  * Used for preparation for ISE
* ports used per switch
  * saved in either text or excel to show status and last change
* Hardware
  * show information about the hardware and stack info
* Port mac vlan ip brand
  * This script outputs an excel file that show the above and status information. 
      Including MAC address brands.
* Unique vlans per switch 
  * Used to generate an overview of which vlans are actually used per switch even though 
      all vlans are known in a L2 domain.
* Substitute vlans
  * A preparation script to swap out an old for a new vlan.

*sw\_cdp\_description isn't finished.*
  This was meant to automatically update descriptions based on CDP information.

### Others
Then there are a few scripts used for different kind of purposes. Have a look at those as well.

## Environment variabels
The python and expect scripts will search for certain environment variables. When present 
it will use these instead of asking for these variables. This will save you a lot of
time. Below is a list of variables used:
* ACSUSER
* ACSPASS
* ACSENABLE
* CISCOCOMMUNITY
* ISERADIUSKEY
* ISEROAMUSER
* ISEROAMPASS

Some of the scripts allow you to call upon these with a prefix as well. This allows you to 
use them e.g. in your lab environment as well without having to adjust your environment 
variables.
If not all variables are known that the script requires it will prompt you for it anyway.
So need to worry if you don't have them all set.
