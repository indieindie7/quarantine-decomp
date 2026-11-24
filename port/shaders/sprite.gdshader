shader_type spatial;
render_mode unshaded, cull_disabled;
uniform sampler2D tex : filter_nearest;
uniform vec2 cam_cell = vec2(-99.0);
uniform bool grid = true;
uniform vec2 anc = vec2(0.0);
uniform sampler2D ordt : filter_nearest;
uniform bool painter = false;
uniform bool idv = false;
varying flat float oid;
varying flat float wnt;
varying flat vec2 fcl;
varying float far;
varying flat float sd;
varying vec2 pix;
varying flat vec4 dims;
varying flat vec2 org;
uniform ivec4 fcam = ivec4(0, -2048, 0, 0);
uniform int fcamz = 0;
uniform float ws = 0.0625;
int tdiv(int a, int b){
	int q = abs(a) / abs(b);
	return ((a < 0) == (b < 0)) ? q : -q;
}
uniform bool prev = false;
uniform sampler2D pal : source_color, filter_nearest;
uniform sampler2D shade : filter_nearest;
vec3 shaded(float i, float depth){
	int lv = int(clamp(floor(depth * 16.0 * 4.0 / 110.0), 0.0, 63.0));
	if (prev) lv = 0;
	int s = int(floor(texelFetch(shade, ivec2(int(i), lv), 0).r * 255.0 + 0.5));
	return texelFetch(pal, ivec2(s, 0), 0).rgb;
}
vec3 shadedlv(float i, float v){
	int lv = int(clamp(floor(v / 64.0), 0.0, 63.0));
	if (prev) lv = 0;
	int s = int(floor(texelFetch(shade, ivec2(int(i), lv), 0).r * 255.0 + 0.5));
	return texelFetch(pal, ivec2(s, 0), 0).rgb;
}
void vertex(){
	vec2 dc = abs(round(COLOR.rg * 255.0) - cam_cell);
	far = (cam_cell.x > -50.0 && max(dc.x, dc.y) > 3.5) ? 1.0 : 0.0;
	vec4 vp = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	sd = -vp.z;
	org = UV;
	oid = CUSTOM0.x;
	fcl = COLOR.rg;
	float siz = abs(UV2.x);
	dims = vec4(round(COLOR.b * 255.0), round(COLOR.a * 255.0), 1.0, 1.0);
	if (grid){
		ivec2 cl = ivec2(round(COLOR.rg * 255.0));
		ivec2 lp = ivec2(floor(VERTEX.xz / ws + 0.5)) - cl * 512;
		int ti = lp.x >> 5;
		int tj = lp.y >> 5;
		int gx = ((fcam.z >> 9) << 9) - fcam.z;
		int gy = ((fcam.w >> 9) << 9) - fcam.w;
		int ox = -((gx * fcam.y + gy * fcam.x) >> 11);
		int oy = (gy * fcam.y - gx * fcam.x) >> 11;
		int cdx = cl.x - (fcam.z >> 9);
		int cdy = cl.y - (fcam.w >> 9);
		int a16 = (-fcam.y * 16) >> 6;
		int b16 = (-fcam.x * 16) >> 6;
		int c16 = (16 * fcam.y) >> 6;
		int bcx = -(cdy * b16 + cdx * a16 + ox);
		int bcy = -(c16 * cdy + b16 * cdx + oy);
		int X = ((-fcam.y * ti) >> 6) + ((-fcam.x * tj) >> 6) - bcx;
		int D = ((-fcam.x * ti) >> 6) + ((tj * fcam.y) >> 6) - bcy;
		int zz = int(floor(-VERTEX.y / ws + 0.5)) - fcamz;
		if (D <= 12){
			far = 1.0;
		}
		else{
			vec2 p = vec2(float(tdiv(X * 256, D) + 160), float(tdiv(zz * 256, D) + 100)) + anc;
			int sc = (int(siz) << 10) / D;
			float wp = float((int(dims.x) * sc) >> 8);
			float hp = float((int(dims.y) * sc) >> 8);
			dims.zw = vec2(max(wp, 1.0), max(hp, 1.0));
			if (wp < 1.0 || hp < 1.0) far = 1.0;
			vec2 c = vec2(UV2.x > 0.0 ? 1.0 : 0.0, UV2.y > 0.5 ? 0.0 : 1.0);
			pix = c * vec2(wp, hp + 1.0);
			vec2 q = vec2(p.x - floor(wp * 0.5), p.y - hp) + pix;
			sd = float(D) / 16.0;
			vec2 nd = vec2(q.x / 160.0 - 1.0, q.y / 100.0 - 1.0);
			/* PROJECTION_MATRIX y points down here */ vec3 vv = vec3((-vp.z * nd.x - PROJECTION_MATRIX[2][0] * vp.z) / PROJECTION_MATRIX[0][0], (-vp.z * nd.y - PROJECTION_MATRIX[2][1] * vp.z) / PROJECTION_MATRIX[1][1], vp.z);
			VERTEX = (inverse(MODELVIEW_MATRIX) * vec4(vv, 1.0)).xyz;
		}
	}
	else{
		vec3 r = normalize(vec3(INV_VIEW_MATRIX[0].x, 0.0, INV_VIEW_MATRIX[0].z));
		float k = siz / 1024.0;
		VERTEX += r * sign(UV2.x) * dims.x * k * 0.5 + vec3(0.0, UV2.y * dims.y * k, 0.0);
		pix = vec2(UV2.x > 0.0 ? 1.0 : 0.0, UV2.y > 0.5 ? 0.0 : 1.0) * dims.xy;
		dims.zw = dims.xy;
	}
}
void fragment(){
	if (far > 0.5) discard;
	DEPTH = FRAGCOORD.z;
	vec2 sp;
	if (grid){
		int W = int(dims.x);
		int H = int(dims.y);
		int wq = int(dims.z);
		int hq = int(dims.w);
		int ci = int(floor(pix.x));
		int rj = int(floor(pix.y));
		int col = ci * (W / wq) + ((ci * (((W % wq) << 10) / wq)) >> 10);
		int row = (rj * ((H << 10) / hq)) >> 10;
		if (row >= H){
			row -= H;
			col += 1;
		}
		if (col >= W || ci >= wq) discard;
		sp = vec2(float(col), float(row));
	}
	else{
		sp = min(floor(floor(pix) * dims.xy / dims.zw + 0.0001), dims.xy - 1.0);
	}
	float i = floor(texelFetch(tex, ivec2(org + sp), 0).r * 255.0 + 0.5);
	if (i < 0.5) discard;
	ALBEDO = shaded(i, sd);
	if (painter && cam_cell.x > -50.0){
		ivec2 oc = ivec2(floor(fcl * 255.0 + 0.5)) - ivec2(cam_cell);
		DEPTH = (texelFetch(ordt, ivec2(int(oid + 0.5), (oc.y + 3) * 7 + oc.x + 3), 0).r + 1.0) / 8192.0;
		if (DEPTH <= 0.0) discard;
		DEPTH += 0.5;
		if (idv) ALBEDO = vec3((oid + 8.0) / 63.0, float((oc.y + 3) * 7 + oc.x + 11) / 63.0, 1.0);
	}
}
