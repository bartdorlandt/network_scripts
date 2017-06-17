#!/usr/bin/perl

# Usage:
# script routername outputfile cmdfile 
# OLD # script routername outputfile cmdfile username password
# If you expect long outputs from the router, make sure you use "ter le 0".

use Net::Telnet;
use Env;

# Set buffer to 10M for output
$buffersize = 10485760;
# timout setting in seconds for output response
$timeoutSecs = 30;

$router = $ARGV[0];
$output = $ARGV[1];
$cmdfile = $ARGV[2];
#$user = $ARGV[3];
#$password = $ARGV[4];
$user = "$ACSUSER";
$password = "$ACSPASS";

# debug if password is being read
#print "\npasswd: $password\n";

# Create a list of commands from a file
if (!-f "$cmdfile") { print "\nfile $cmdfile does not exist!\n"; exit 1; }
open(CMDS, "$cmdfile") or die "Can't open $cmdfile : $!";
while(<CMDS>) {
        $cmd = $_;
        chomp($cmd);
        if ($cmd ne "") {
               push @cmds, $cmd;
        }
}
close CMDS;

# Router prompt for matching (Uppercase)
#$prompt = uc($router).'#';
# Need to figure out how all the hostnames are set up and adjust the prompt accordingly.
#$prompt = uc($router)'#';
$prompt = /^SW[0-9]{4,6}/.'#';

#print $prompt;

$telnet = new Net::Telnet(Timeout => $timoutSecs);
#login debug
#$telnet->input_log($output);
$telnet->max_buffer_length($buffersize);
$telnet->open($router);
$telnet->waitfor('/Username:/i');
$telnet->print($user);
$telnet->waitfor('/Password:/i');
$telnet->print($password);
$telnet->waitfor("/$prompt/");
#Start output
$telnet->input_log($output);
foreach $cmd (@cmds){
        $telnet->print($cmd);
        $telnet->waitfor("/$prompt/");
}
$telnet->close;

