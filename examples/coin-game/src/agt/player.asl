{ include( "vesna.asl" ) }

my_points( 0 ).
coin_res( Color, Res ) :- area( Color, coin( Res ) ).
coin_on_my_side( Res ) :- coin_res( Color, Res ) & team( Color )[ source( self ) ].
coin_on_other_side( Res ) :- coin_res( Color, Res ) & not team( Color )[ source( self ) ].
enemy_res( Color, Res ) :- area( Color, enemy( Res ) ).
enemy_on_my_side( Enemy ) :- area( Color, enemy( Enemy ) ) & team( Color )[ source( self ) ].

concat([ ], L, L).
concat([H|T], L, [H|M]) :- concat(T, L, M).

+!start
    :   .my_name( Me ) & team( Color )
    <-  .broadcast( askOne, team( Team ) );
        +my_pos( Color );
        .wait( 1000 );
        !play.

+?team(Team)
    :   team( Team )[ source( self ) ]
    <-  true.

@play1[ offensive( 50 ), defensive( 100 ) ]
+!play
    :   coin_on_my_side( Resource )
    <-  .print( "I go gain ", Resource, " in my midfield" );
        vesna.walk( Resource );
        .wait( {+movement( Status, Reason ) }, 10000, play );
        if ( Status == reached_destination ) {
            .print( "I arrived!" );
        } else {
            .print( "Somebody else took the money" );
            -area( _, coin( Resource ) );
        }
        !play.

@play2[ offensive( 100 ), defensive( 5 ) ]
+!play
    :   coin_on_other_side( Resource )
    <-  .print( "I go gain ", Resource, " in the other midfield" );
        vesna.walk( Resource );
        .wait( {+movement( Status, Reason ) }, 10000, play );
        if ( Status == reached_destination ) {
            .print( "I arrived!" );
        } else {
            .print( "Somebody else took the money" );
            -area( _, coin( Resource ) );
        }
        !play.

@play3[ offensive( 10 ), defensive( 100 ) ]
+!play
    :   enemy_on_my_side( Enemy )
    <-  .print( "Oh, there is an enemy! I go attack it!" );
        vesna.walk( Enemy );
        .wait( {+movement( completed, destination_reached ) }, 10000, play );
        .print( "I arrived!" );
        !play.


@play5[ offensive( 20 ), defensive( 100 ) ]
+!play
    :   team( Color )[ source( self ) ] & not my_pos( Color )
    <-  .print( "I have nothing to do BUT I am not on my side!" );
        vesna.walk( Color );
        .wait( {+movement( Status, Reason ) }, 10000, play );
        .print( Status, Reason );
        .print( "I arrived!" );
        !play.

@play4[ offensive( 5 ), defensive( 75 ) ]
+!play
    :   team( Color )[ source( self ) ] & my_pos( Color )
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
