extends NavigationRegion3D

@export var scene_to_spawn: PackedScene
@export var spawn_area_min: Vector3 = Vector3(-5, 0, -4.5)
@export var spawn_area_max: Vector3 = Vector3(5, 5, 4.5)
@export var min_spawn_time: float = 10.0
@export var max_spawn_time: float = 20.0
@export var coin_script : Script

var coin_counter : int = 0

var connected_players : int = 0
var total_players : int = 0

func _ready():
	spawn_loop()
	for player in get_tree().get_nodes_in_group( "Agents" ):
		if player.is_visible_in_tree():
			total_players += 1

func spawn_loop():
	var wait_time = randf_range(min_spawn_time, max_spawn_time)
	print( "Waiting for " + str( wait_time ) )
	await get_tree().create_timer(wait_time).timeout
	spawn_object()
	spawn_loop() # Chiamata ricorsiva per continuare

func spawn_object():
	if not scene_to_spawn:
		return
	#if not connected_players == len( get_tree().get_nodes_in_group( "Agents" ) ):
		#return
	if not connected_players == total_players:
		return
	var instance = scene_to_spawn.instantiate()
	var rand_x = randf_range(spawn_area_min.x, spawn_area_max.x)
	var rand_z = randf_range(spawn_area_min.z, spawn_area_max.z)
	instance.global_transform.origin = Vector3(rand_x, 0.2, rand_z)
	instance.scale = Vector3( 0.4, 0.4, 0.4 )
	instance.set_script( coin_script )
	instance.add_to_group( "coins" )
	instance.name = "coin" + str( coin_counter )
	coin_counter += 1
	add_child(instance)
	get_tree().call_group("Agents", "on_object_spawned", instance)
		
func connected_player():
	connected_players += 1
