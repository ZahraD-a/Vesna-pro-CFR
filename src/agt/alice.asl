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


@p1[temper( [ prop1( 0.0 ), prop2( 0.3 ) ] ), effects( [ prop3( 0.7 ), prop4( -0.05 ) ] ) ]
+!p
    :   true
    <-  .print( "ciao" ).

@p2[temper( [ prop3( 0.2 ), prop2( 0.3 ) ] ), effects( [ prop3( -0.1 ), prop4( 0.2 ) ] ) ]
+!p
    :   true
    <-  .print( "ciao ciao" ).
