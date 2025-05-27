{ include( "vesna.asl" ) }

my_points( 0 ).

+!start
    :   .my_name( Me ) & team( Color )
    <-  .broadcast( askOne, team( Team ) );
        +my_pos( Color );
        .wait( 1000 );
        !play.

@play1[ offensive( 50 ), defensive( 100 ) ]
+!play
    :   area( Color, Resource ) & team( Color )[ source( self ) ] & Resource \== enemy( _ )
    <-  .print( "I go gain ", Resource, " in my midfield" );
        vesna.walk( Resource );
        .wait( {+movement( completed, destination_reached ) }, 2000, play );
        .print( "I arrived!" );
        !play.

@play2[ offensive( 100 ), defensive( 5 ) ]
+!play
    :   area( Color, Resource ) & not team( Color )[ source( self ) ] & Resource \== enemy( _ )
    <-  .print( "I go gain ", Resource, " in the other midfield" );
        vesna.walk( Resource );
        .wait( {+movement( completed, destination_reached ) }, 2000, play );
        .print( "I arrived!" );
        !play.

@play3[ offensive( 10 ), defensive( 100 ) ]
+!play
    :   area( Color, enemy( Enemy ) ) & team( Color )[ source( self ) ] 
    <-  .print( "Oh, there is an enemy! I go attack it!" );
        vesna.walk( Enemy );
        .wait( {+movement( completed, destination_reached ) }, 2000, play );
        .print( "I arrived!" );
        !play.


@play5[ offensive( 20 ), defensive( 100 ) ]
+!play
    :   team( Color )[ source( self ) ] & not my_pos( Color )
    <-  .print( "I have nothing to do BUT I am not on my side!" );
        vesna.walk( Color );
        .wait( {+movement( completed, destination_reached ) }, 2000, play );
        .print( "I arrived!" );
        !play.

@play4[ offensive( 5 ), defensive( 75 ) ]
+!play
    :   true
    <-  .print( "I do nothing" );
        .wait( 1000 );
        !play.

+gained( Resource )
    :   my_points( X ) & .my_name( Me ) & team( Color )[ source( self ) ] & my_pos( Color )
    <-  .broadcast( signal, gained( Me, Resource ) );
        -+my_points( X + 1 ).

+gained( Resource )
    :   my_points( X ) & .my_name( Me ) & team( Color )[ source( self ) ] & not my_pos( Color )
    <-  .broadcast( signal, gained( Me, Resource ) );
        -+my_points( X + 2 ).

+gained( Ag, Res )
    :   not .my_name( Ag )
    <-  -area( _, Res );
        .drop_all_desires;
        .drop_all_intentions;
        !play.

+malus( N )
    :   my_points( Points )
    <-  -+my_points( Points - N ).

+new_pos( Color )
    :   .my_name( Me )
    <-  -+my_pos( Color );
        .broadcast( signal, pos(Me, Color ) ).

+pos( Ag, Color )
    :   not .my_name( Ag ) & not team( Color )[ source( self ) ]
    <-  -+area( Color, enemy( Ag ) ).
