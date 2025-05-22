extends Node3D

@export var rotation_speed_deg: float = 45.0 # gradi al secondo

func _process(delta):
	rotate_y(deg_to_rad(rotation_speed_deg * delta))
