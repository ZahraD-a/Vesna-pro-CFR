extends CharacterBody3D

const SPEED = 5.0
const ACCELERATION = 8.0
const JUMP_VELOCITY = 4.5

@export var PORT : int
var tcp_server := TCPServer.new()
var ws := WebSocketPeer.new()

var regions_dict : Dictionary = {}
var current_region = ""

var end_communication = true

var target_movement : String = "empty"
var global_target_node : Node3D
var global_target_pos : Vector3

var gained_coin : bool = false

@onready var navigator : NavigationAgent3D = $NavigationAgent3D
@onready var jump_anim = $Body/Jump
@onready var idle_anim = $Body/Idle
@onready var run_anim = $Body/Run

var my_pos : String

#@export var desired_separation: float = 3.0  # distanza minima desiderata
#@export var separation_weight: float = 5.0   # peso della forza di separazione

func _ready() -> void:
	if position.x < 0:
		my_pos = "blue"
	else:
		my_pos = "red"
	if tcp_server.listen( PORT ) != OK:
		push_error( "Unable to start the srver" )
		set_process( false )
	play_idle()
	
func _process(delta: float) -> void:
	while tcp_server.is_connection_available():
		var conn : StreamPeerTCP = tcp_server.take_connection()
		assert( conn != null )
		get_node( "/root/Node3D/NavigationRegion3D" ).call( "connected_player" )
		ws.accept_stream( conn )
		
	ws.poll()
	
	if ws.get_ready_state() == WebSocketPeer.STATE_OPEN:
		while ws.get_available_packet_count():
			var msg : String = ws.get_packet().get_string_from_ascii()
			print( "Received msg ", msg )
			var intention : Dictionary = JSON.parse_string( msg )
			manage( intention )
			
func navigate( delta: float ) -> void:
	if navigator.is_target_reached() or navigator.is_navigation_finished():
		play_idle()
		velocity.x = 0
		velocity.z = 0
		if not end_communication:
			signal_end_movement( 'completed', 'destination_reached' )
			
	elif not navigator.is_navigation_finished():
		play_run()
		var final_direction = ( navigator.get_next_path_position() - global_position ).normalized()
		rotation.y = atan2( final_direction.x, final_direction.z)
		
		velocity = velocity.lerp( final_direction * SPEED, ACCELERATION * delta )
	
	move_and_slide()
	
func signal_mind( type: String, data: Dictionary ):
	var log : Dictionary = {}
	log[ 'sender' ] = 'body'
	log[ 'receiver' ] = 'vesna'
	log[ 'type' ] = type
	log[ 'data' ] = data
	ws.send_text( JSON.stringify( log ) )

func _physics_process(delta: float) -> void:
	# Add the gravity.
	if not is_on_floor():
		velocity += get_gravity() * delta
	
	navigate( delta )
	
	var changed : bool = false
	if global_position.z < 0 and my_pos != "blue":
		my_pos = "blue"
		changed = true
	elif global_position.z > 0 and my_pos != "red":
		my_pos = "red"
		changed = true
	if changed:
		var log : Dictionary = {}
		log[ 'sender' ] = 'body'
		log[ 'receiver' ] = 'vesna'
		log[ 'type' ] = 'env'
		var data : Dictionary = {}
		data[ 'type' ] = 'pos'
		data[ 'color' ] = my_pos
		log[ 'data' ] = data
		ws.send_text( JSON.stringify( log ) )
		
	
	for i in range(get_slide_collision_count()):
		var collision = get_slide_collision(i)
		var collider = collision.get_collider()
		if ( collider.name.begins_with( "coin" ) ):
			gained_coin = true
			collider.queue_free()
			var log : Dictionary = {}
			log[ 'sender' ] = 'body'
			log[ 'receiver' ] = 'vesna'
			log[ 'type' ] = 'coin'
			var data : Dictionary = {}
			data[ 'type' ] = 'gain'
			data[ 'name' ] = collision.get_collider().name
			log[ 'data' ] = data
			ws.send_text( JSON.stringify( log ) )
		elif collider.is_in_group( "Agents" ):
			if self.is_in_group( "red_team" ) and collider.is_in_group( "blue_team" ) and global_position.z < 0:
				var log : Dictionary = {}
				log[ 'sender' ] = 'body'
				log[ 'receiver' ] = 'vesna'
				log[ 'type' ] = 'coin'
				var data : Dictionary = {}
				data[ 'type' ] = 'malus'
				data[ 'amount' ] = 1
				log[ 'data' ] = data
				ws.send_text( JSON.stringify( log ) )
				position = Vector3( 0, 0.5, 4.5 )
				navigator.target_position = global_position
			elif self.is_in_group( "blue_team" ) and collider.is_in_group( "red_team" ) and global_position.z > 0:
				var log : Dictionary = {}
				log[ 'sender' ] = 'body'
				log[ 'receiver' ] = 'vesna'
				log[ 'type' ] = 'coin'
				var data : Dictionary = {}
				data[ 'type' ] = 'malus'
				data[ 'amount' ] = 1
				log[ 'data' ] = data
				ws.send_text( JSON.stringify( log ) )
				position = Vector3( 0, 0.5, -4.5 )
				navigator.target_position = global_position
	
#func _on_area_body_entered( region_name, body ):
	#if ( body.name == self.name ):
		#print( "Agent ", self.name, " entered region ", region_name )
		#if ( region_name == target_movement ):
			#signal_end_movement( 'completed', 'destination_reached' )
			#navigator.set_target_position( global_position )
	
func _exit_tree() -> void:
	ws.close()
	tcp_server.stop()
	
#func get_avoidance_force() -> Vector3:
	#var force: Vector3 = Vector3.ZERO
	## Supponiamo che tutti i CharacterBody3D siano nel gruppo "players"
	#for other in get_tree().get_nodes_in_group("agents"):
		#if other == self:
			#continue
		#var diff = global_transform.origin - other.global_transform.origin
		#var distance = diff.length()
		#if distance < desired_separation and distance > 0:
			## La forza cresce quando la distanza diminuisce
			#force += diff.normalized() / distance
	#return force * separation_weight

func manage( intention : Dictionary ) -> void:
	var sender : String = intention[ 'sender' ]
	var receiver : String = intention[ 'receiver' ]
	var type : String = intention[ 'type' ]
	var data : Dictionary = intention[ 'data' ]
	if type == 'walk':
		if data[ 'type' ] == 'goto':
			var target : String = data[ 'target' ]
			if data.has( 'id' ):
				var id : int = data[ 'id' ]
				walk( target, id )
			else:
				walk( target, -1 )
	elif type == 'interact':
		if data[ 'type' ] == 'use':
			var art_name : String = data[ 'art_name' ]
			use( art_name )
		elif data[ 'type' ] == 'grab':
			var art_name : String = data[ 'art_name' ]
			grab( art_name )
		elif data[ 'type' ] == 'free':
			var art_name : String = data[ 'art_name' ]
			free_art( art_name )
		elif data[ 'type' ] == 'release':
			var art_name : String = data[ 'art_name' ]
			release( art_name )

func walk( target, id ):
	var target_node = get_node_or_null( "/root/Node3D/NavigationRegion3D/" + target)
	if not target_node:
		target_node = get_node_or_null( "/root/Node3D/" + target )
	if not target_node:
		return
	navigator.set_target_position( target_node.global_position )
	target_node.connect( "tree_exited", Callable( self, "_on_target_destroyed" ) )
	target_movement = target
	global_target_node = target_node
	play_run()
	end_communication = false

func get_obj_from_group( art_name : String, group_name : String ):
	var group_objs = get_tree().get_nodes_in_group( group_name )
	for group_obj in group_objs:
		if art_name == group_obj.name:
			return group_obj
	return null
	
func use( art_name: String ):
	print( "I want to use " + art_name )
	
func grab( art_name: String ):
	var art = get_obj_from_group( art_name, "GrabbableArtifact")
	if art == null:
		print( "Object not found!")
		return
	print( "I take the hand" )
	var right_hand = get_node_or_null( "Body/Root/Skeleton3D/RightHand" )
	if ( right_hand == null ):
		print( "Oh no I do not have a hand!")
	#art.global_position = Vector3.ZERO
	art.reparent( right_hand )
	print( "reparent done" )
	#art.global_transform.origin = right_hand.position
	art.transform.origin = Vector3.ZERO
	print( "I want to grab " + art_name )

func free_art( art_name : String ):
	print( "I free " + art_name )
	
func release( art_name : String ):
	var release_points = get_tree().get_nodes_in_group( "ReleasePoint" )
	var nearest_release
	var nearest_dist = 1000
	for release_point in release_points:
		var cur_dist = release_point.global_position.distance_to( global_position )
		if  cur_dist < nearest_dist:
			nearest_release = release_point
			nearest_dist = cur_dist
	var art = get_obj_from_group( art_name, "GrabbableArtifact" )
	art.reparent( nearest_release )
	art.transform.origin = Vector3.ZERO
	print( "I release " + art_name )
	
func signal_end_movement( status : String, reason : String ) -> void:
	target_movement = "empty"
	var log : Dictionary = {}
	log[ 'sender' ] = 'body'
	log[ 'receiver' ] = 'vesna'
	log[ 'type' ] = 'signal'
	var msg : Dictionary = {}
	msg[ 'type' ] = 'movement'
	msg[ 'status' ] = status
	msg[ 'reason' ] = reason
	log[ 'data' ] = msg
	ws.send_text( JSON.stringify( log ) )
	end_communication = true

func update_region( new_region : String ) -> void:
	current_region = new_region
	if current_region not in regions_dict:
		regions_dict[ current_region ] = []
		
func play_idle() -> void:
	if run_anim and run_anim.is_playing():
		run_anim.stop()
	idle_anim.play( "Root|Idle" )

func play_run() -> void:
	if idle_anim.is_playing():
		idle_anim.stop()
	run_anim.play( "Root|Run" )
	
func on_object_spawned( new_object ):
	var log : Dictionary = {}
	log[ 'sender' ] = 'body'
	log[ 'receiver' ] = 'vesna'
	log[ 'type' ] = 'coin'
	var msg : Dictionary = {}
	msg[ 'type' ] = 'spawn'
	msg[ 'name' ] = 'coin( ' + new_object.name + ')'
	if new_object.global_transform.origin.z < 0:
		msg[ 'midfield' ] = 'blue'
	else:
		msg[ 'midfield' ] = 'red'
	log[ 'data' ] = msg
	
	ws.send_text( JSON.stringify( log ) )
	
func _on_target_destroyed():
	if not gained_coin:
		signal_end_movement( 'stopped', 'target_destroyed' )
	gained_coin = false
