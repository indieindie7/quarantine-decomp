class_name FpsGraph
extends Control
## 240 frame-time bars, 60/30 fps guide lines, text "fps X avg Y worst Z". F3 toggles.
var ft: PackedFloat32Array = PackedFloat32Array()
const N := 240
func _ready() -> void:
	custom_minimum_size = Vector2(N + 8, 78); size = custom_minimum_size; position = Vector2(8, 8)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
## 11-20 hitch log: every frame over 25 ms -> user://fps.log (or env GOOBI_FPSLOG) with script times + sim events; summary on exit.
static var ev: String = ""
static var us: Array = [0, 0, 0, 0]
static var ticks: int = 0
var _log: FileAccess
var _all: PackedFloat32Array = PackedFloat32Array()
var _t: float = 0.0
var _pp: float = 0.0
var _ph: float = 0.0
## whole-tree split of a frame: all nodes' _physics_process / all nodes' _process / the rest (engine + render)
var _pq: int = 0
var _fq: int = 0
var _tp: int = 0
var _tf: int = 0
class Tail extends Node:
	var g: FpsGraph
	func _physics_process(_d: float) -> void: g._tp += Time.get_ticks_usec() - g._pq
	func _process(_d: float) -> void: g._tf = Time.get_ticks_usec() - g._fq
func _enter_tree() -> void:
	var tl := Tail.new(); tl.g = self; tl.process_priority = 100000; tl.process_physics_priority = 100000; add_child(tl)
	get_tree().physics_frame.connect(func(): _pq = Time.get_ticks_usec())
	get_tree().process_frame.connect(func(): _fq = Time.get_ticks_usec())
static func note(e: String) -> void:
	if ev.length() < 120: ev += e + " "
static func phys(sim: int, evs: int, sync: int, rest: int) -> void:
	us[0] += sim; us[1] += evs; us[2] += sync; us[3] += rest; ticks += 1
func _exit_tree() -> void:
	if _log == null or _all.size() < 10: return
	var a: Array = Array(_all); a.sort()
	var sum: float = 0.0
	for x in a: sum += x
	var n1: int = maxi(1, a.size() / 100); var low: float = 0.0
	for i in n1: low += a[a.size() - 1 - i]
	_log.store_line("SUMMARY frames %d avg %.1f fps 1%%low %.1f fps worst %.1f ms over25ms %d | avg script proc %.2f phys %.2f ms" % [a.size(), a.size() / sum, n1 / low, a[-1] * 1000.0, a.filter(func(x): return x > 0.025).size(), _pp / a.size() * 1000.0, _ph / a.size() * 1000.0])
	_log.close()
func _process(dt: float) -> void:
	ft.append(dt)
	_t += dt; _all.append(dt); _pp += Performance.get_monitor(Performance.TIME_PROCESS); _ph += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)
	if _log == null:
		var lp: String = OS.get_environment("GOOBI_FPSLOG")
		_log = FileAccess.open(lp if lp != "" else "user://fps.log", FileAccess.WRITE)
	if dt > 0.025 and _log != null:
		_log.store_line("t %.2f dt %.1f ms | ticks %d sim %.1f ev %.1f sync %.1f rest %.1f ms | tree: phys %.1f proc(prev) %.1f ms | draws %d | %s" % [_t, dt * 1000.0, ticks, us[0] / 1000.0, us[1] / 1000.0, us[2] / 1000.0, us[3] / 1000.0, _tp / 1000.0, _tf / 1000.0, int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)), ev])
		_log.flush()
	ev = ""; us = [0, 0, 0, 0]; ticks = 0; _tp = 0
	if ft.size() > N: ft.remove_at(0)
	queue_redraw()
func _unhandled_key_input(e: InputEvent) -> void:
	var k := e as InputEventKey
	if k != null and k.pressed and not k.echo and k.keycode == KEY_F3: visible = not visible
func _draw() -> void:
	draw_rect(Rect2(0, 0, N + 8, 78), Color(0, 0, 0, 0.55))
	var sc: float = 50.0 / 0.05  # px per second: 50 px = 50 ms
	var worst: float = 0.0; var sum: float = 0.0
	for i in ft.size():
		var t: float = ft[i]; worst = maxf(worst, t); sum += t
		var h: float = minf(t * sc, 50.0)
		var c := Color(0.3, 0.9, 0.3) if t <= 1.0 / 58.0 else (Color(0.95, 0.8, 0.2) if t <= 1.0 / 28.0 else Color(0.95, 0.25, 0.2))
		draw_rect(Rect2(4 + i, 62 - h, 1, h), c)
	draw_line(Vector2(4, 62 - sc / 60.0), Vector2(N + 4, 62 - sc / 60.0), Color(1, 1, 1, 0.35))
	draw_line(Vector2(4, 62 - sc / 30.0), Vector2(N + 4, 62 - sc / 30.0), Color(1, 1, 1, 0.2))
	var avg: float = sum / maxf(ft.size(), 1.0)
	var fnt := ThemeDB.fallback_font
	draw_string(fnt, Vector2(6, 74), "fps %d avg %d worst %d" % [Engine.get_frames_per_second(), int(1.0 / maxf(avg, 0.0001)), int(1.0 / maxf(worst, 0.0001))], HORIZONTAL_ALIGNMENT_LEFT, -1, 11)
