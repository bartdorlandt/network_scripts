cat >> $OUTPUTFILE << EOF
! 
! Last part of the configuration
aaa new-model
!
aaa authentication fail-message @

  ****************************** - WARNING - ***************************
  *                                                                    *
  *     Your attempt to access this system/network has failed.         *
  *                                                                    *
  *     If you are an unauthorized person, LOG OFF IMMEDIATELY         *
  *                                                                    *
  *     Unauthorized access to this system/network is                  *
  *                                                                    *
  *     strictly prohibited!                                           *
  *                                                                    *
  ****************************** - WARNING - ***************************

@
aaa authentication login default group tacacs+ local
aaa authentication enable default group tacacs+ enable
aaa authorization config-commands
aaa authorization exec default group tacacs+ if-authenticated
aaa authorization network default group tacacs+ if-authenticated
aaa accounting exec default start-stop group tacacs+
aaa accounting commands 1 default start-stop group tacacs+
aaa accounting commands 2 default start-stop group tacacs+
aaa accounting commands 5 default start-stop group tacacs+
aaa accounting commands 15 default start-stop group tacacs+
aaa accounting network default start-stop group tacacs+
aaa accounting system default start-stop group tacacs+
aaa authorization commands 1 default group tacacs+ if-authenticated
aaa authorization commands 2 default group tacacs+ if-authenticated
aaa authorization commands 5 default group tacacs+ if-authenticated
aaa authorization commands 15 default group tacacs+ local
!
EOF
