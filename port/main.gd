extends Node3D
## Quarantine city viewer. Args after `--`: --city=CITY --shot=<png> --frames=N --top --bg --pos=x,y,z --yaw=deg --rotdir=-1
## Data: res://data/<CITY>.json + _walls.png from Quarantine/tools/cityexport.py. Game x -> X, y -> Z, z (down) -> -Y. 1 game unit = 1/16 m.
const S := 1.0 / 16.0
var city := "CITY"
var shot := ""
var frames := 30
var top := false
var nofps := false
var rotdir := 1
var fov := 75.0
var voff := 1.0
var anc := Vector2.ZERO
var cab_on := true
var rotate := 0  ## Q.EXE 0x4736c: blocks are never rotated; cell bits 8-9 pick 1 of 4 texture sets
var cam: Camera3D
var yaw := 0.0
var pitch := 0.0
var n := 0

func _ready() -> void:
	var pos := Vector3.ZERO
	var has_pos := false
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--city="): city = a.substr(7)
		elif a.begins_with("--shot="): shot = a.substr(7)
		elif a.begins_with("--frames="): frames = int(a.substr(9))
		elif a.begins_with("--dmg="): dmg_raw = int(a.substr(6))
		elif a.begins_with("--odo="): odom = int(a.substr(6))
		elif a.begins_with("--g2="): gauge2 = int(a.substr(5))
		elif a.begins_with("--icon="): car_icon = int(a.substr(7))
		elif a.begins_with("--blips="):
			for b in a.substr(8).split(","): var v := b.split(":"); blips.append([int(v[0]), int(v[1]), int(v[2])])
		elif a == "--top": top = true
		elif a == "--nofps": nofps = true
		elif a == "--rotate": rotate = 1
		elif a.begins_with("--fov="): fov = float(a.substr(6))
		elif a == "--nocab": cab_on = false
		elif a.begins_with("--anc="): anc = Vector2(float(a.substr(6).split(",")[0]), float(a.substr(6).split(",")[1]))
		elif a.begins_with("--voff="): voff = float(a.substr(7))
		elif a.begins_with("--res="): var rs := a.substr(6).split("x"); get_window().size = Vector2i(int(rs[0]), int(rs[1]))
		elif a == "--bg": DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_MINIMIZED)
		elif a.begins_with("--rotdir="): rotdir = int(a.substr(9))
		elif a.begins_with("--yaw="): yaw = deg_to_rad(float(a.substr(6)))
		elif a.begins_with("--pos="):
			var p := a.substr(6).split(","); pos = Vector3(float(p[0]), float(p[1]), float(p[2])); has_pos = true
	if not ("--bg" in OS.get_cmdline_user_args()):  # project starts minimized + no_focus (test renders never take focus); normal play restores
		get_window().set_flag(Window.FLAG_NO_FOCUS, false); DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED); get_window().grab_focus()
	for a2 in OS.get_cmdline_user_args():
		if a2.begins_with("--frot="): floor_rot = int(a2.substr(7))
		if a2.begins_with("--frow="): frow = int(a2.substr(7))
		if a2 == "--nodosfloor": dosfloor = false
		if a2 == "--nodoswall": doswall = false
		if a2 == "--nowtab": wtab = false
		if a2.begins_with("--fshift="): floor_shift = int(a2.substr(9))
		if a2 == "--fswap": floor_swap = true
		if a2 == "--fmir": floor_mir = true
		if a2 == "--nocull": far_cull = false
		if a2.begins_with("--ents="): ents_path = a2.substr(7)
		if a2 == "--cullflip": cullflip = false
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/%s.json" % city))
	if FileAccess.file_exists("res://areas/%s.txt" % city) and not ("--noarea" in OS.get_cmdline_user_args() or "--noarea" in OS.get_cmdline_args()):  # editable area file (tools/areas.py) wins over the JSON cells
		var ac: Array = []; var aw := 0; var ah := 0
		for al in FileAccess.get_file_as_string("res://areas/%s.txt" % city).split(String.chr(10)):
			var at := al.strip_edges().split(" ", false)
			if at.size() == 0 or at[0].begins_with("#"): continue
			if at[0] == "area": aw = int(at[2]); ah = int(at[3]); continue
			for ax in at: ac.append(0 if ax == "...." else ax.hex_to_int())
		if aw > 0 and ac.size() == aw * ah: d["w"] = aw; d["h"] = ah; d["cells"] = ac; print("area file loaded: ", city, " ", aw, "x", ah)
		else: push_error("area file %s.txt bad size, JSON cells used" % city)
	var only_area := ""
	for a3 in OS.get_cmdline_user_args():
		if a3.begins_with("--area="): only_area = a3.substr(7)
	if ResourceLoader.exists("res://areas/%s.tscn" % city) and not "--noarea" in OS.get_cmdline_user_args():  # map scene = one instanced scene per area (tools/areas.py split); wins over the whole-map txt
		area_map = load("res://areas/%s.tscn" % city).instantiate(); var full: Array = []; full.resize(int(d["w"]) * int(d["h"])); full.fill(0)
		for an in area_map.get_children():
			if not an.has_method("read_cells"): continue
			if only_area != "" and an.name != only_area: an.visible = false; continue  # baked preview meshes of the other areas must not show (found by tools/sceneparity.py 11-23)
			var ar: Dictionary = an.read_cells(); var part: Array = []; part.resize(full.size()); part.fill(0)
			if ar["cells"].size() != int(ar["w"]) * int(ar["h"]): push_error("area %s bad size" % an.name); continue
			for ay in int(ar["h"]):
				for ax2 in int(ar["w"]):
					var gi: int = (int(ar["oy"]) + ay) * int(d["w"]) + int(ar["ox"]) + ax2; part[gi] = ar["cells"][ay * int(ar["w"]) + ax2]; full[gi] = part[gi]
			area_cells[an] = part
		d["cells"] = full; print("area scenes loaded: ", city, " ", area_cells.size())
	g_cells = d["cells"]; g_blocks = d["blocks"]; g_w = int(d["w"]); g_h = int(d["h"])
	if FileAccess.file_exists("res://data/%s_bsp.json" % city) and not "--nopainter" in OS.get_cmdline_user_args(): bsp = JSON.parse_string(FileAccess.get_file_as_string("res://data/%s_bsp.json" % city))
	if "--test" in OS.get_cmdline_user_args(): run_tests(); return
	for ac in OS.get_cmdline_user_args():  # --chk=<file>: per-pose painter order for tools/chkparity.py (checksum parity, NOTES "CHECKSUM PARITY")
		if ac.begins_with("--chk="): run_chk(ac.substr(6)); return
	painter = not bsp.is_empty() and not top
	var img := Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_walls_idx.png" % city))
	var palt := ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_pal.png" % city)))
	var shdt := ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_shade.png" % city)))
	# UV = repeat coords, UV2 = atlas cell (tile, file); floors repeat in world space (Q.EXE 0x4a6e4: tile = 64 << flag units)
	var wsh := Shader.new()
	# palette-index atlas -> distance shade LUT (Q.EXE 0x82770, level = min(63, depth * 4 / 110)) -> 6-bit DAC palette
	# DOS shade (table 0x98430, value = depth * 256 / 110, row = value >> 6): wall 0x425ec = linear in screen x between the first and last point of the WHOLE wall (ends clipped at depth 12, int step); floor polygon 0x4a6e4 = linear in screen y between top and bottom vertex (clipped at depth 15). CUSTOM0/1 = wall ends / quad corners xz
	wsh.code = FileAccess.get_file_as_string("res://shaders/wall.gdshader")  # shaders live in port/shaders/*.gdshader, one statement per line (split 11-23, tools/shfmt.py)
	mat = ShaderMaterial.new(); mat.shader = wsh; mat.set_shader_parameter("tex", ImageTexture.create_from_image(img)); mat.set_shader_parameter("pal", palt); mat.set_shader_parameter("cullflip", cullflip); mat.set_shader_parameter("doswall", doswall); mat.set_shader_parameter("shade", shdt)
	set_anim(mat)
	if area_map != null:
		add_child(area_map)
		for an in area_cells:
			var dd: Dictionary = d.duplicate(); dd["cells"] = area_cells[an]; var ami: MeshInstance3D = an.get_node_or_null("walls"); if ami == null: ami = MeshInstance3D.new(); ami.name = "walls"; an.add_child(ami)
			ami.mesh = build(dd); ami.material_override = mat; ami.extra_cull_margin = 16384.0
	else:
		var mi := MeshInstance3D.new(); mi.mesh = build(d); mi.material_override = mat; add_child(mi)
	var oimg := Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_objs_idx.png" % city))
	if oimg != null and d.has("spr"):
		var sh := Shader.new()
		# DOS sprite scaler (Q.EXE 0x48c90): scale = (size << 10) / depth, w = (sw * scale) >> 8, h = (sh * scale) >> 8, x0 = px - w / 2, y0 = py - h, skipped when depth <= 12; drawn on the 320x200 pixel grid
		sh.code = FileAccess.get_file_as_string("res://shaders/sprite.gdshader")
		sm = ShaderMaterial.new(); sm.shader = sh; sm.set_shader_parameter("tex", ImageTexture.create_from_image(oimg)); sm.set_shader_parameter("pal", palt); sm.set_shader_parameter("shade", shdt); sm.set_shader_parameter("grid", not top); sm.set_shader_parameter("anc", anc)
		if ents_path != "" and not top: setup_ents()
		if area_map != null:
			for an in area_cells:
				var dd: Dictionary = d.duplicate(); dd["cells"] = area_cells[an]; var aom: MeshInstance3D = an.get_node_or_null("objs"); if aom == null: aom = MeshInstance3D.new(); aom.name = "objs"; an.add_child(aom)
				aom.mesh = build_objs(dd); aom.material_override = sm; aom.extra_cull_margin = 16384.0
		else:
			var om := MeshInstance3D.new(); om.mesh = build_objs(d); om.material_override = sm; om.extra_cull_margin = 16384.0; add_child(om)
	var w: int = d["w"]; var h: int = d["h"]
	var gm := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(w * 32.0, h * 32.0); gm.mesh = pm
	gm.position = Vector3(w * 16.0, -20.0 * S - 0.05, h * 16.0)
	var g2 := StandardMaterial3D.new(); g2.albedo_color = Color(0, 0, 0); g2.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; gm.material_override = g2; add_child(gm)
	var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0, 0, 0)
	var simg := Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_sky.png" % city))
	if simg != null and not top:
		# DOS sky: <pre>SKY.IMG 320x200, row = screen row, column = (x + dx) % 320, dx = 3 - head * 2 / 9 (fit on q_018 + q_020, NOTES 11-22 SKY FIT)
		env.background_mode = Environment.BG_CANVAS; env.background_canvas_max_layer = -1
		var sl := CanvasLayer.new(); sl.layer = -1; add_child(sl)
		var tr := TextureRect.new(); tr.texture = ImageTexture.create_from_image(simg); tr.stretch_mode = TextureRect.STRETCH_SCALE; tr.set_anchors_preset(Control.PRESET_FULL_RECT)
		var ssh := Shader.new(); ssh.code = FileAccess.get_file_as_string("res://shaders/sky.gdshader")
		skym = ShaderMaterial.new(); skym.shader = ssh; skym.set_shader_parameter("sky", tr.texture); tr.material = skym; sl.add_child(tr)
	var cimg := Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_cab.png" % city))
	if cimg != null and not top and cab_on:  # CAB.IMG cockpit frame over the view (index 0 = window)
		var cl := CanvasLayer.new(); cl.layer = 1; add_child(cl)
		var ct := TextureRect.new(); ct.texture = ImageTexture.create_from_image(cimg); ct.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST; ct.set_anchors_preset(Control.PRESET_FULL_RECT); ct.stretch_mode = TextureRect.STRETCH_SCALE; ct.mouse_filter = Control.MOUSE_FILTER_IGNORE; cl.add_child(ct)
		var wimg := Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_wheel.png" % city))
		if wimg != null:  # WHEELSPR.SPR steering wheel + hands: 7 frames 140x47, frame 3 = straight, at 89,153
			var ov := Image.create(320, 200, false, Image.FORMAT_RGBA8); wimg.convert(Image.FORMAT_RGBA8); ov.blit_rect(wimg, Rect2i(0, 3 * 47, 140, 47), Vector2i(89, 153))
			var rimg := Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_radar.png" % city))
			if rimg != null:  # RADAR2.SPR [0x830f8]: radar frame glyph 0xb at 176,3 + centre dot 0xa at 197,16 (0x35150), car icon glyph [0x82348] at 240,5 (0x35f0c)
				rimg.convert(Image.FORMAT_RGBA8); var rs: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/radar2.json"))
				ov.blit_rect(rimg, Rect2i(int(rs[0xb][0]), 0, int(rs[0xb][1]), int(rs[0xb][2])), Vector2i(176, 3))
				for g in blips: ov.blend_rect(rimg, Rect2i(int(rs[g[0]][0]), 0, int(rs[g[0]][1]), int(rs[g[0]][2])), Vector2i(g[1], g[2]))  # radar blips (0x35150, masked blit 0x25c2c), --blips=glyph:x:y,..
				for g in [[0xa, 197, 16], [car_icon, 240, 5]]: ov.blit_rect(rimg, Rect2i(int(rs[g[0]][0]), 0, int(rs[g[0]][1]), int(rs[g[0]][2])), Vector2i(g[1], g[2]))
			var fimg := Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_font.png" % city))
			if fimg != null:  # CABFONT.SPR dash text, positions matched on DOS shot q_048 (start state): $ money at 10,160 (digits 17 + 6n, 161), clock mm:ss at 16 + 6n,169, counters
				fimg.convert(Image.FORMAT_RGBA8); var fs: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/cabfont.json")); var gl: Array = [[11, 10, 160]]
				var ms := "%05d" % money; for n in 5: gl.append([ms.unicode_at(n) - 48, 17 + 6 * n, 161])
				var cs := "%02d:%02d" % [clock_s / 60, clock_s % 60]; for n in 5: gl.append([10 if n == 2 else cs.unicode_at(n) - 48, 16 + 6 * n, 169])
				gl.append_array([[0, 34, 180], [13, 104, 11], [13, 108, 11], [13, 112, 11], [0x80 + ((16 - int(fposmod(rad_to_deg(yaw) - 180.0 + 0.01, 360.0)) * 4 / 45) & 31), 138, 11], [0, 272, 28], [0, 276, 28], [0, 280, 28]])
				var dp := dmg_raw >> 2; var db := 0x4a if dmg_raw < 0x78 else (0x40 if dmg_raw < 0xf0 else 0x36)  # damage percent, Q.EXE 0x3547c
				if dp / 100 == 0: gl.append_array([[0x54, 265, 6], [db + dp % 100 / 10, 273, 6], [db + dp % 10, 282, 6]])
				else: gl.append_array([[0x36, 273, 6], [0x36, 282, 6], [0x37, 265, 6]])
				gl.append_array([[0x22 + odom / 100 % 10, 178, 144], [0x22 + odom % 100 / 10, 186, 144], [0x22 + odom % 10, 194, 144], [0x17 + gauge2 / 10 % 10, 126, 142], [0x17 + gauge2 % 10, 134, 142]])  # odometer 0x35744, gauge 0x35c9c
				for g in gl: ov.blit_rect(fimg, Rect2i(int(g[0]) % 16 * 24, int(g[0]) / 16 * 16, int(fs[int(g[0])][0]), int(fs[int(g[0])][1])), Vector2i(int(g[1]), int(g[2])))
			var yimg := Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_wayp.png" % city)); var timg := Image.load_from_file(ProjectSettings.globalize_path("res://data/%s_font2.png" % city))
			if yimg != null and timg != null:  # fare panel, Q.EXE 0x34a44 (screen y = draw y + 150): WAYP2.SPR [0x7f388] arrows 0-7 lit / 8-15 dark at table 0x7786a, '.' glyph 0x15 at 278,178, km digits 0x16 + d at 270/274/282/286,178; status text = FONT2 glyphs (ASCII - 32) at 270,172, 4 px pitch. 'KM' is part of the cab picture
				yimg.convert(Image.FORMAT_RGBA8); timg.convert(Image.FORMAT_RGBA8); var ys: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/wayp2.json")); var yl: Array = [[0x15, 278, 178]]
				var ap := [[280, 157], [293, 163], [302, 171], [293, 184], [280, 190], [266, 184], [256, 171], [266, 163]]
				for n in 8: yl.append([n if n == fare_arrow else n + 8, ap[n][0], ap[n][1]])
				var km := int(fare_km * 100.0); yl.append_array([[0x16 + km / 1000 % 10, 270, 178], [0x16 + km / 100 % 10, 274, 178], [0x16 + km / 10 % 10, 282, 178], [0x16 + km % 10, 286, 178]])
				for g in yl: ov.blit_rect(yimg, Rect2i(int(ys[g[0]][0]), 0, int(ys[g[0]][1]), int(ys[g[0]][2])), Vector2i(g[1], g[2]))
				var ft := "FOR HIRE"; for n in ft.length(): ov.blit_rect(timg, Rect2i((ft.unicode_at(n) - 32) * 4, 0, 4, 5), Vector2i(270 + 4 * n, 172))
			var wt := TextureRect.new(); wt.texture = ImageTexture.create_from_image(ov); wt.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST; wt.set_anchors_preset(Control.PRESET_FULL_RECT); wt.stretch_mode = TextureRect.STRETCH_SCALE; wt.mouse_filter = Control.MOUSE_FILTER_IGNORE; cl.add_child(wt)
	var we := WorldEnvironment.new(); we.environment = env; add_child(we)
	cam = Camera3D.new(); cam.far = 4000.0; cam.fov = fov; cam.keep_aspect = Camera3D.KEEP_WIDTH; add_child(cam); cam.current = true
	if not top and voff != 0.0:  # DOS 3D view sits 1 px lower than a centred frustum (NOTES 11-22 SHIFT FIT)
		var fs := 2.0 * cam.near * tan(deg_to_rad(fov) * 0.5); cam.set_frustum(fs, Vector2(0, voff * fs / 320.0), cam.near, cam.far); cam.keep_aspect = Camera3D.KEEP_WIDTH
	if top:
		cam.projection = Camera3D.PROJECTION_ORTHOGONAL; cam.size = h * 32.0 if not has_pos else pos.y
		cam.position = Vector3(w * 16.0, 500.0, h * 16.0) if not has_pos else Vector3(pos.x, 500.0, pos.z)
		cam.rotation = Vector3(-PI / 2.0, 0, 0)
	else:
		cam.position = pos if has_pos else Vector3(w * 16.0, 0.5, h * 16.0)
		cam.rotation = Vector3(0, yaw, 0)
	var cl := CanvasLayer.new(); add_child(cl)
	if not nofps: cl.add_child(load("res://view/fps_graph.gd").new())  ## --nofps only for parity shots
	if shot == "": Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

var mat: ShaderMaterial
var skym: ShaderMaterial
var sm: ShaderMaterial
var far_cull: bool = true
## Animated wall textures (Q.EXE 0x89100 table, state bytes 0x893b2, tools/animexport.py): --anim=s0,s1,.. = frame per anim (parity snaps carry the DOS states); the shader swaps the atlas cell.
func set_anim(m: ShaderMaterial) -> void:
	var f := "res://data/%s_anim.json" % city
	if not FileAccess.file_exists(f): return
	var a: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(f)); var st: PackedStringArray = []
	for x in OS.get_cmdline_user_args():
		if x.begins_with("--anim="): st = x.substr(7).split(",")
	var fr: Array = []; var to: Array = []
	for k in a["from"].size():
		var s: int = int(st[k]) if k < st.size() else 0; var fs: Array = a["frames"][k]
		if s < 0 or s >= fs.size(): s = 0
		fr.append(Vector2i(int(a["from"][k][0]), int(a["from"][k][1]))); to.append(Vector2i(int(fs[s][0]), int(fs[s][1])))
	while fr.size() < 20: fr.append(Vector2i(-1, -1)); to.append(Vector2i(-1, -1))
	m.set_shader_parameter("anim_from", fr); m.set_shader_parameter("anim_to", to); m.set_shader_parameter("anim_n", a["from"].size())
var area_map: Node = null
var area_cells: Dictionary = {}
var cullflip: bool = true  # viewed par_rf: this winding keeps the walls DOS draws
var floor_rot: int = 0
var money: int = 10
var fare_km: float = 0.0
var clock_s: int = 0
var dmg_raw: int = 400  # DOS [0x836d0] short; percent = raw >> 2 (dash 0x3547c)
var odom: int = 0  # DOS [0x81394] short, odometer (0x35744)
var gauge2: int = 0  # DOS [0x82344] short, 2-digit gauge at 126,142 (0x35c9c)
var blips: Array = []  # radar blips [glyph, x, y] (tools/paritylib.py blips(); live list 0x82ea8 not ported)
var car_icon: int = 0  # DOS [0x82348] short, RADAR2 glyph of the car icon at 240,5 (0x35f0c)
var fare_arrow: int = -1  # DOS short [0x7ea10]: lit direction arrow 0-7, -1 none (0x34a44)
var frow: int = 0
var ents: Array = []  # live DOS entities (tools/entdump.py), drawn by Q.EXE 0x33fb8 rules
var ents_path: String = ""
var ent_mi: MeshInstance3D
var return_tex: bool = false
var em: ShaderMaterial
var ent_cell: Dictionary = {}
func setup_ents() -> void:
	ents = JSON.parse_string(FileAccess.get_file_as_string(ents_path))
	var atl: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/ents_atlas.json"))
	var sh := Shader.new(); sh.code = FileAccess.get_file_as_string("res://shaders/ent.gdshader")  # = sprite.gdshader + entity scaler 0x33fb8 changes (was patched in at run time until 11-23)
	em = ShaderMaterial.new(); em.shader = sh
	if not return_tex: em.set_shader_parameter("tex", ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://data/ents_idx.png"))))
	em.set_shader_parameter("elut", ImageTexture.create_from_image(Image.create_from_data(256, 144, false, Image.FORMAT_L8, FileAccess.get_file_as_bytes("res://data/ent_lut.bin"))))
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES); st.set_custom_format(0, SurfaceTool.CUSTOM_RGBA_FLOAT)
	for e in ents:
		var cx: int = int(e["x"]) >> 9; var cy: int = int(e["y"]) >> 9
		if cx < 0 or cy < 0 or cx >= g_w or cy >= g_h: continue
		var bi: int = (int(g_cells[cy * g_w + cx]) & 0x7f) - 1
		if bi < 0: continue
		var key: int = cy * g_w + cx
		if not ent_cell.has(key): ent_cell[key] = []
		var k: int = ent_cell[key].size(); var b: Dictionary = g_blocks[bi]
		ent_cell[key].append([k, int(e["x"]) & 0x1ff, int(e["y"]) & 0x1ff, int(e["z"])])
		var c := Vector3(float(e["x"]), -float(e["z"]), float(e["y"])) * S
		for pt in e["parts"]:
			if not atl.has(pt[0]) or int(pt[1]) < 0 or int(pt[1]) >= atl[pt[0]].size(): continue
			var r: Array = atl[pt[0]][int(pt[1])]
			if int(r[2]) == 0: continue
			for q in [[-1, 1], [1, 1], [1, 0], [-1, 1], [1, 0], [-1, 0]]:
				st.set_custom(0, Color(float(b["q"].size() + b["w"].size() + b["o"].size() + k), float(pt[2]), float(pt[3]), float(int(e["mirror"]) * 100 + int(e["shade"]) + 1)))
				st.set_color(Color(cx / 255.0, cy / 255.0, float(r[2]) / 255.0, float(r[3]) / 255.0)); st.set_uv(Vector2(float(r[0]), float(r[1]))); st.set_uv2(Vector2(float(e["size"]) * q[0], float(q[1]))); st.add_vertex(c)
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = em; mi.extra_cull_margin = 16384.0; add_child(mi); ent_mi = mi;
var bsp: Array = []  # per-block BSP trees dumped live by tools/bspdump.py (Q.EXE 0x4668c painter order)
var painter: bool = true
var g_cells: Array = []
var g_blocks: Array = []
var g_w: int = 0
var g_h: int = 0
var ordtex: ImageTexture
var ord_key := Vector3i(-1, -1, -99999)
var ord_buf: PackedFloat32Array
func run_chk(path: String) -> void:  # one tick per stored pose: keys (cell row * ORD_W + item column) the port draws, in the port's draw order
	var out: Array = []
	for po in JSON.parse_string(FileAccess.get_file_as_string("res://tests/vectors/draworder.json")):
		var c: Array = po["cam"]; var h: int = posmod(int(c[3]), 5760); bsp_order(int(c[0]), int(c[1]), int(c[2]), -dsin(h), dsin(h + 1440))
		var it: Array = []
		for k in ord_buf.size():
			if ord_buf[k] >= 0.0: it.append([ord_buf[k], k])
		it.sort_custom(func(a, b): return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]))
		var keys: Array = []; var ties := 0
		for i in it.size():
			keys.append(int(it[i][1]))
			if i > 0 and it[i][0] == it[i - 1][0]: ties += 1
		out.append({"name": po["name"], "order": keys, "ties": ties, "sin": [dsin(h), dsin(h + 1440)]})
	var f := FileAccess.open(path, FileAccess.WRITE); f.store_string(JSON.stringify(out)); f.close()
	print("CHK wrote %d poses" % out.size()); set_process(false); get_tree().quit(0)
func run_tests() -> void:  # --test: expected values from the DOS side (tools/mkvectors.py -> tests/vectors) against this file's own code
	var bad := 0; var V := "res://tests/vectors/"
	var ds: Array = JSON.parse_string(FileAccess.get_file_as_string(V + "dsin.json")); var nb := 0
	for r in ds:
		if dsin(int(r[0])) != int(r[1]):
			nb += 1
			if nb <= 5: print("TEST dsin FAIL h=%d port=%d dos=%d" % [int(r[0]), dsin(int(r[0])), int(r[1])])
	print("TEST dsin %s %d/%d" % ["ok" if nb == 0 else "FAIL", ds.size() - nb, ds.size()]); bad += nb
	for po in JSON.parse_string(FileAccess.get_file_as_string(V + "draworder.json")):
		var c: Array = po["cam"]; var h: int = posmod(int(c[3]), 5760); bsp_order(int(c[0]), int(c[1]), int(c[2]), -dsin(h), dsin(h + 1440))
		var last := -1.0; var seen := 0; var inv := 0; var exp: Dictionary = {}
		for it in po["seq"]:
			var k: int = int(it[0]) * ORD_W + int(it[1]); exp[k] = true
			if int(it[1]) >= ORD_W: continue
			var v: float = ord_buf[k]
			if v < 0.0: continue  # cell culled by the port (0x4736c view cull): only the relative order of what is drawn counts
			seen += 1
			if v <= last:
				inv += 1
				if inv <= 3: print("TEST draworder FAIL %s row=%d col=%d port=%d after %d" % [po["name"], int(it[0]), int(it[1]), int(v), int(last)])
			last = v
		var extra := 0
		for k2 in ord_buf.size():
			if ord_buf[k2] >= 0.0 and not exp.has(k2): extra += 1
		if extra > 0: print("TEST draworder FAIL %s: %d items drawn by the port that DOS does not list" % [po["name"], extra])
		print("TEST draworder %s %s drawn %d of %d" % [po["name"], "ok" if inv + extra == 0 else "FAIL", seen, po["seq"].size()]); bad += inv + extra
	print("TEST RESULT %s (%d bad)" % ["PASS" if bad == 0 else "FAIL", bad])
	set_process(false); get_tree().quit(1 if bad > 0 else 0)
const ORD_W := 128
const CELL_ORD: Array[int] = [-3,-3,3,-3,3,3,-3,3,-2,-3,2,-3,3,-2,3,2,2,3,-2,3,-3,2,-3,-2,-1,-3,1,-3,3,-1,3,1,1,3,-1,3,-3,1,-3,-1,0,-3,3,0,0,3,-3,0,-2,-2,2,-2,2,2,-2,2,-1,-2,1,-2,2,-1,2,1,1,2,-1,2,-2,1,-2,-1,0,-2,2,0,0,2,-2,0,-1,-1,1,-1,1,1,-1,1,0,-1,1,0,0,1,-1,0,0,0]  # Q.EXE table 0x7acca
func bsp_order(camx: int, camy: int, camz: int, sn: int, cs: int) -> void:  # Q.EXE 0x4736c cell loop + 0x4668c tree walk + 0x464d0 leaf sort -> draw-list index per (cell row, item)
	var k := Vector3i(camx, camy, camz * 8192 + sn + 2048 + (cs + 2048) * 4096 * 8192)
	if k == ord_key: return
	ord_key = k
	var buf := PackedFloat32Array(); buf.resize(ORD_W * 49); buf.fill(-1.0)
	var n_ord: int = 0; var ccx: int = camx >> 9; var ccy: int = camy >> 9
	for e in 49:
		var dx: int = CELL_ORD[e * 2]; var dy: int = CELL_ORD[e * 2 + 1]; var cx: int = ccx + dx; var cy: int = ccy + dy
		if cx < 0 or cy < 0 or cx >= g_w or cy >= g_h or n_ord >= 600: continue
		var rx: int = cx * 512 + 256 - camx; var ry: int = cy * 512 + 256 - camy  # Q.EXE 0x4736c cell cull: view x / depth of the cell centre
		var vx: int = (-cs * rx - sn * ry) >> 11; var vd: int = ((-sn * rx + cs * ry) >> 11) + 0x101
		if vd <= 0 or (maxi(absi(vx) - 0x100, 0) << 8) / vd >= 0xa0: continue
		var bi: int = (int(g_cells[cy * g_w + cx]) & 0x7f) - 1
		if bi < 0 or bi >= bsp.size(): continue
		var nodes: Array = bsp[bi]["nodes"]
		if nodes.is_empty(): continue
		var nq: int = int(bsp[bi]["nQ"]); var nw: int = int(bsp[bi]["nW"]); var ob: Array = g_blocks[bi]["o"]
		var lx: int = (camx & 0x1ff) - dx * 512; var ly: int = (camy & 0x1ff) - dy * 512; var row: int = ((dy + 3) * 7 + dx + 3) * ORD_W
		var eleaf: Dictionary = {}; var no: int = ob.size()
		for ee in ent_cell.get(cy * g_w + cx, []):
			var en: int = 0
			while true:
				var eq: Array = nodes[en]; var ekd: int = int(eq[0])
				if ekd == 1: break
				var et: bool = ((ee[2] - int(eq[6])) * int(eq[4]) + int(eq[3]) * (ee[1] - int(eq[5])) < 0) if ekd == 0 else (int(eq[6]) < ee[3])
				var enx: int = int(eq[8]) if et else int(eq[7])
				if enx < 0: break
				en = enx
			if not eleaf.has(en): eleaf[en] = []
			eleaf[en].append(ee)
		var stack: Array[int] = [0]
		while not stack.is_empty():
			var v: int = stack.pop_back(); var nd: Array = nodes[v >> 1]; var kind: int = int(nd[0])
			if v & 1:
				var it: int = int(nd[1]) + (nq if kind == 0 else 0)
				if it < ORD_W: buf[row + it] = float(n_ord)
				n_ord += 1
				for ee in eleaf.get(v >> 1, []):
					if nq + nw + no + ee[0] < ORD_W: buf[row + nq + nw + no + ee[0]] = float(n_ord)
					n_ord += 1
				continue
			if kind == 1:
				var ol: Array = []
				for oi in nd[1]:
					var o: Array = ob[int(oi)]; var ax: int = lx - int(o[0]); var ay: int = ly - int(o[1]); var az: int = camz - (int(o[2]) - 1)
					ol.append([ax * ax + ay * ay + az * az, int(oi)])
				for ee in eleaf.get(v >> 1, []):
					var ex: int = lx - ee[1]; var ey: int = ly - ee[2]; var ez: int = camz - ee[3]
					ol.append([ex * ex + ey * ey + ez * ez, no + ee[0]])
				for gap in [3, 1]:  # DOS leaf sort 0x464d0 = Watcom qsort 0x5490d small path (n < 16): gap 3 over items 3, 6, 9.. then gap 1 insertion, far first; this fixes the order of equal distances
					var sp: int = gap
					while sp < ol.size():
						var sq: int = sp
						while sq > 0 and ol[sq][0] > ol[sq - gap][0]:
							var st: Array = ol[sq]; ol[sq] = ol[sq - gap]; ol[sq - gap] = st; sq -= gap
						sp += gap
				for oe in ol:
					if nq + nw + oe[1] < ORD_W: buf[row + nq + nw + oe[1]] = float(n_ord)
					n_ord += 1
				continue
			var a_first: bool = ((ly - int(nd[6])) * int(nd[4]) + int(nd[3]) * (lx - int(nd[5])) < 0) if kind == 0 else (int(nd[6]) < camz)
			var f: int = int(nd[7]) if a_first else int(nd[8]); var g: int = int(nd[8]) if a_first else int(nd[7])
			if g >= 0: stack.push_back(g * 2)
			stack.push_back((v >> 1) * 2 + 1)
			if f >= 0: stack.push_back(f * 2)
	ord_buf = buf
	var im := Image.create_from_data(ORD_W, 49, false, Image.FORMAT_RF, buf.to_byte_array())
	if ordtex == null: ordtex = ImageTexture.create_from_image(im)
	else: ordtex.update(im)
	if mat != null: mat.set_shader_parameter("ordt", ordtex)
	if sm != null: sm.set_shader_parameter("ordt", ordtex)
var wtab := true  # DOS table view transform for wall points (0x372c0 + 0x37368 + 0x373e0)
var doswall := true  # DOS integer wall rasteriser emulation (0x482fc + 0x425ec), NOTES 11-22 WALL COLUMN MATH
var dosfloor := true  # DOS integer floor filler (0x47d10 + 0x4a6e4 + 0x3c664), proven by tools/floorref.py; --nodosfloor = float floor
var floor_shift: int = 0
var floor_swap: bool = false
var floor_mir: bool = false
var sintab: PackedByteArray
func dsin(h: int) -> int:  # Q.EXE 0x36f14: quarter table 0x77964, 1441 shorts, sin * 2048, heading unit 1/16 deg
	if sintab.is_empty(): sintab = FileAccess.get_file_as_bytes("res://data/sintab.bin")
	h = posmod(h, 5760); var q: int = h / 1440; var r: int = h % 1440
	match q:
		0: return sintab.decode_s16(r * 2)
		1: return sintab.decode_s16((1440 - r) * 2)
		2: return -sintab.decode_s16(r * 2)
	return -sintab.decode_s16((1440 - r) * 2)
func rot(p: Vector2, r: int) -> Vector2:
	for i in posmod(r * rotdir, 4) * rotate: p = Vector2(512.0 - p.y, p.x)
	return p

func uv(f: int, t: int, u: float, v: float) -> Vector2:
	return Vector2(clampf(u, 0.001, 0.999), clampf(v, 0.001, 0.999))

## Block objects (12-byte recs x,y,z,0,type,size): Q.EXE 0x48c90 screen-aligned sprite, world size = sprite px * size / 64, anchor bottom centre.
func build_objs(d: Dictionary) -> ArrayMesh:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES); st.set_custom_format(0, SurfaceTool.CUSTOM_RGBA_FLOAT)
	var w: int = d["w"]; var h: int = d["h"]
	var cells: Array = d["cells"]; var blocks: Array = d["blocks"]; var spr: Array = d["spr"]
	for cy in h:
		for cx in w:
			var bi: int = (int(cells[cy * w + cx]) & 0x7f) - 1  # cell block N = file block N-1, 0 = empty (live table 0x7aeb8)
			if bi < 0: continue
			var b: Dictionary = blocks[bi]
			for oi in b["o"].size():
				var o: Array = b["o"][oi]
				var t: int = int(o[4]) & 0xff
				if t >= spr.size(): continue
				var r: Array = spr[t]
				if int(r[2]) == 0: continue
				var k: float = float(o[5]) / 64.0 * S
				var hw: float = float(r[2]) * k * 0.5; var hh: float = float(r[3]) * k
				var c := Vector3(cx * 512.0 + float(o[0]), -float(o[2]), cy * 512.0 + float(o[1])) * S
				var u0: float = (float(r[0]) + 0.01) / 1024.0; var u1: float = (float(r[0]) + float(r[2]) - 0.01) / 1024.0
				var v0: float = (float(r[1]) + 0.01) / 1024.0; var v1: float = (float(r[1]) + float(r[3]) - 0.01) / 1024.0
				var Q := [[-hw, hh, u0, v0], [hw, hh, u1, v0], [hw, 0.0, u1, v1], [-hw, 0.0, u0, v1]]
				for i in [0, 1, 2, 0, 2, 3]: st.set_custom(0, Color(float(b["q"].size() + b["w"].size() + oi), 0, 0, 0)); st.set_color(Color(cx / 255.0, cy / 255.0, float(r[2]) / 255.0, float(r[3]) / 255.0)); st.set_uv(Vector2(float(r[0]), float(r[1]))); st.set_uv2(Vector2(float(o[5]) * signf(Q[i][0]), 1.0 if Q[i][1] > 0.0 else 0.0)); st.add_vertex(c)  # COLOR.ba = sprite w,h px; UV = atlas origin px; UV2 = (+-size, top)
	return st.commit()

func build(d: Dictionary) -> ArrayMesh:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES); st.set_custom_format(0, SurfaceTool.CUSTOM_RGBA_FLOAT); st.set_custom_format(1, SurfaceTool.CUSTOM_RGBA_FLOAT); st.set_custom_format(2, SurfaceTool.CUSTOM_RGBA_FLOAT)
	var w: int = d["w"]; var h: int = d["h"]
	var cells: Array = d["cells"]; var blocks: Array = d["blocks"]
	var cu := [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]
	for cy in h:
		for cx in w:
			var c: int = int(cells[cy * w + cx])
			if (c & 0x7f) == 0: continue
			var b: Dictionary = blocks[(c & 0x7f) - 1]
			var r: int = (c >> 8) & 3
			var o := Vector2(cx * 512.0, cy * 512.0)
			for qi in b["q"].size():
				var q: Array = b["q"][qi]
				var P: Array = []
				for v in 4:
					var p: Vector2 = rot(Vector2(q[5 + v * 2], q[6 + v * 2]), r) + o
					P.append(Vector3(p.x, -float(q[3]), p.y) * S)
				var U: Array = []
				var ts: float = 64.0 * pow(2.0, float(int(q[4]) + floor_shift))
				var cell2 := Vector2(int(q[1][r]), int(q[0]))
				for v in 4:
					var wp := Vector2(P[v].x, P[v].z) / S / ts
					match (int(q[2]) + floor_rot) & 3:
						0: U.append(wp)
						1: U.append(Vector2(wp.y, -wp.x))
						2: U.append(-wp)
						3: U.append(Vector2(-wp.y, wp.x))
					if floor_mir: U[v].x = -U[v].x
					if floor_swap: U[v] = Vector2(U[v].y, U[v].x)
				for i in [0, 1, 2, 0, 2, 3]: st.set_custom(2, Color(float(qi), 0, 0, 0)); st.set_custom(0, Color(P[0].x, P[0].z, P[1].x, P[1].z)); st.set_custom(1, Color(P[2].x, P[2].z, P[3].x, P[3].z)); st.set_color(Color(cx / 255.0, cy / 255.0, 0, float(((int(q[2]) + floor_rot) & 3) + 4 * (int(q[4]) + floor_shift)) / 255.0)); st.set_uv(U[i]); st.set_uv2(cell2); st.add_vertex(P[i])
			for wi in b["w"].size():
				var wl: Array = b["w"][wi]
				var nseg: int = int(wl[0])
				var tx: Array = wl[8][r]
				var w0: Vector2 = (rot(Vector2(wl[4], wl[5]), r) + o) * S; var w1: Vector2 = (rot(Vector2(wl[4] + wl[1] * nseg, wl[5] + wl[2] * nseg), r) + o) * S
				for i in nseg:
					var a: Vector2 = rot(Vector2(wl[4] + wl[1] * i, wl[5] + wl[2] * i), r) + o
					var e: Vector2 = rot(Vector2(wl[4] + wl[1] * (i + 1), wl[5] + wl[2] * (i + 1)), r) + o
					var zb: float = -float(wl[6]); var zt: float = zb + float(wl[3])
					var f: int = 0; var t: int = 0
					var ti: int = nseg - 1 - i  # Q.EXE 0x487b8 stores wall points end -> start, tex k = k-th segment from the END, U runs end -> start
					if ti < tx.size(): f = int(tx[ti][0]); t = int(tx[ti][1])
					var rf: int = f; var rt: int = t  # wall seen from behind (two-sided): 0x487b8 swaps the point table, texture list stays -> tex k = k-th segment from the START
					if i < tx.size(): rf = int(tx[i][0]); rt = int(tx[i][1])
					var vt: float = 1.0 - float(wl[3]) / 64.0
					var P2 := [Vector3(a.x, zt, a.y) * S, Vector3(e.x, zt, e.y) * S, Vector3(e.x, zb, e.y) * S, Vector3(a.x, zb, a.y) * S]
					var U2 := [uv(f, t, 1, vt), uv(f, t, 0, vt), uv(f, t, 0, 1), uv(f, t, 1, 1)]
					# Q.EXE 0x482fc: wall skipped when its last point is left of its first on screen, unless flags[file*14+tile] & 2 (first tex entry); COLOR.b 0.5 = one-sided, 1 = two-sided
					var two: bool = false
					if tx.size() > 0 and d.has("wf") and int(tx[0][0]) < 15 and int(tx[0][1]) < 12: two = (int(d["wf"][int(tx[0][0])][int(tx[0][1])]) & 2) != 0
					for k in [0, 1, 2, 0, 2, 3]: st.set_custom(2, Color(float(b["q"].size() + wi), 1.0 if wl.size() > 9 and int(wl[9]) < 0 else 0.0, rt, rf)); st.set_custom(0, Color(w0.x, w0.y, w1.x, w1.y)); st.set_custom(1, Color(nseg, ti, wl[6] - wl[3], wl[6])); st.set_color(Color(cx / 255.0, cy / 255.0, 1.0 if two else 0.5, k / 255.0)); st.set_uv(U2[k]); st.set_uv2(Vector2(t, f)); st.add_vertex(P2[k])
	return st.commit()

func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		yaw -= e.relative.x * 0.003; pitch = clampf(pitch - e.relative.y * 0.003, -1.5, 1.5)
		cam.rotation = Vector3(pitch, yaw, 0)
	elif e is InputEventKey and e.pressed and e.keycode == KEY_ESCAPE: get_tree().quit()

## --bake: save every area's meshes + editor preview materials (no DOS screen emulation, no distance shade) next to the area scenes; tools/areas.py bake wires them into the .tscn so the world shows in the Godot editor.
func bake_areas() -> void:
	var bd := "res://areas/%s/" % city; var n := 0
	var pm: ShaderMaterial = mat.duplicate(); pm.set_shader_parameter("prev", true); pm.set_shader_parameter("doswall", false); pm.set_shader_parameter("dosfloor", false); pm.set_shader_parameter("cam_cell", Vector2(-99.0, -99.0)); ResourceSaver.save(pm, bd + "_walls_preview.res")
	if sm != null:
		var ps: ShaderMaterial = sm.duplicate(); ps.set_shader_parameter("prev", true); ps.set_shader_parameter("grid", false); ps.set_shader_parameter("cam_cell", Vector2(-99.0, -99.0)); ResourceSaver.save(ps, bd + "_objs_preview.res")
	for an in area_cells:
		for nm in ["walls", "objs"]:
			var m: MeshInstance3D = an.get_node_or_null(nm)
			if m != null and m.mesh != null and m.mesh.get_surface_count() > 0: ResourceSaver.save(m.mesh, bd + "%s_%s.res" % [an.name, nm]); n += 1
	print("baked ", city, " meshes ", n)
var bake_pending: bool = "--bake" in OS.get_cmdline_user_args()
func _process(dt: float) -> void:
	if bake_pending and area_map != null: bake_pending = false; bake_areas()
	if mat != null and cam != null:  # DOS floor filler inputs (Q.EXE 0x4a6e4): 0x7eabc = cos h * 2048, 0x7eab8 = -sin h * 2048 (h = yaw - 180 deg), 0x83224/8 = cam x,y, camz
		var hh := cam.rotation.y - PI; var hd16: int = posmod(int(round(rad_to_deg(hh) * 16.0)), 5760); var fcv := Vector4i(-dsin(hd16), dsin(hd16 + 1440), int(floor(cam.position.x / S)), int(floor(cam.position.z / S))); mat.set_shader_parameter("fcam", fcv); if sm != null: sm.set_shader_parameter("fcam", fcv); sm.set_shader_parameter("fcamz", int(round(-cam.position.y / S)))
		mat.set_shader_parameter("hdeg", hd16 >> 4); mat.set_shader_parameter("fcamz", int(round(-cam.position.y / S))); mat.set_shader_parameter("frow", frow); mat.set_shader_parameter("dosfloor", dosfloor); mat.set_shader_parameter("wtab", wtab)
	if far_cull and cam != null and cam.projection != Camera3D.PROJECTION_ORTHOGONAL:
		var cc := Vector2(floorf(cam.position.x / S / 512.0), floorf(cam.position.z / S / 512.0))
		if mat != null: mat.set_shader_parameter("cam_cell", cc)
		if painter and mat != null:
			bsp_order(int(floor(cam.position.x / S)), int(floor(cam.position.z / S)), int(round(-cam.position.y / S)), -dsin(posmod(int(round(rad_to_deg(cam.rotation.y - PI) * 16.0)), 5760)), dsin(posmod(int(round(rad_to_deg(cam.rotation.y - PI) * 16.0)), 5760) + 1440)); mat.set_shader_parameter("painter", true)
			if sm != null: sm.set_shader_parameter("painter", true)
			for ka in OS.get_cmdline_user_args():
				if ka.begins_with("--kil="): mat.set_shader_parameter("kil", Vector2i(int(ka.substr(6).split(",")[0]), int(ka.substr(6).split(",")[1])))
			if "--idv" in OS.get_cmdline_user_args():
				mat.set_shader_parameter("idv", true)
				if sm != null: sm.set_shader_parameter("idv", true)
		if sm != null: sm.set_shader_parameter("cam_cell", cc)
	if not top and shot == "":
		var v := Vector3(Input.get_axis(&"ui_left", &"ui_right"), 0, Input.get_axis(&"ui_up", &"ui_down"))
		if Input.is_physical_key_pressed(KEY_W): v.z -= 1
		if Input.is_physical_key_pressed(KEY_S): v.z += 1
		if Input.is_physical_key_pressed(KEY_A): v.x -= 1
		if Input.is_physical_key_pressed(KEY_D): v.x += 1
		cam.position += cam.global_transform.basis * v * dt * (60.0 if Input.is_physical_key_pressed(KEY_SHIFT) else 15.0)
	if skym != null: skym.set_shader_parameter("dx", float(4 * ((6000 - (posmod(roundi((rad_to_deg(cam.rotation.y) - 180.0) * 16.0), 5760) & 0xfff0) / 18) % 80)))  # Q.EXE 0x3f85c: Mode X sky, 4 px steps
	if em != null and sm != null:
		for u in ["pal", "shade", "grid", "anc", "fcam", "fcamz", "cam_cell", "ordt", "painter", "idv", "ws", "prev"]:
			var uv = sm.get_shader_parameter(u)
			if uv != null: em.set_shader_parameter(u, uv)
	n += 1
	if shot != "" and n == frames:
		get_viewport().get_texture().get_image().save_png(shot); get_tree().quit()
