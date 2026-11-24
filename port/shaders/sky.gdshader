shader_type canvas_item;
uniform float dx = 0.0;
uniform sampler2D sky : filter_nearest, repeat_enable;
void fragment(){
	COLOR = vec4(texture(sky, vec2(fract(UV.x + dx / 320.0), UV.y)).rgb, 1.0);
}
