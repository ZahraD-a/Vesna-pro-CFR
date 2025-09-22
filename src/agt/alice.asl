+!start
    <-  !p;
        .wait( 1000 );
        !p;
        .wait( 1000 );
        !!p;
        !!p;
        .wait( 1000 );
        !p;
        vesna.walk;
        vesna.rotate( left );
        vesna.jump.


@p1[temper( [ prop1( 0 ), prop2( 30 ) ] ), effects( [ prop1( 10 ), prop2( -5 ) ] ) ]
+!p
    :   true
    <-  .print( "ciao" ).

@p2[temper( [ prop1( 20 ), prop2( 30 ) ] ), effects( [ prop1( -10 ), prop2( 20 ) ] ) ]
+!p
    :   true
    <-  .print( "ciao ciao" ).
