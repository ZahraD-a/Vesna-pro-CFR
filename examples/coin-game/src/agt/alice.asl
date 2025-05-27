+!start
    <-  !p;
        .wait( 1000 );
        !p;
        .wait( 1000 );
        !p;
        .wait( 1000 );
        !p.


@p1[propensions( [ prop1( 20 ), prop2( 30 ) ] )]
+!p
    :   true
    <-  .print( "ciao" ).

@p2[propensions( [ prop1( 10 ), prop2( 30 ) ] )]
+!p
    :   true
    <-  .print( "ciao ciao" ).
