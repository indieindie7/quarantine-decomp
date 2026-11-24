shader_type spatial;
render_mode unshaded, cull_disabled;
uniform sampler2D tex : filter_nearest;
uniform vec2 cam_cell = vec2(-99.0);
uniform bool cullflip = false;
uniform bool dosfloor = true;
uniform bool doswall = false;
uniform bool wtab = true;
uniform sampler2D ordt : filter_nearest;
uniform bool painter = false;
uniform bool idv = false;
uniform ivec2 kil = ivec2(-1);
varying flat float oid;
varying flat float wnt;
varying flat vec2 wtile;
varying flat ivec4 wa;
varying flat ivec4 wb;
uniform int hdeg = 0;
uniform ivec4 fcam = ivec4(0, -2048, 0, 0);
uniform int fcamz = 0;
uniform int frow = 0;
uniform float fsign = 1.0;
uniform bool fdsw = false;
uniform float ws = 0.0625;
varying float far;
varying flat vec3 sh;
varying flat vec3 fq;
varying flat vec4 fc0;
varying flat vec4 fc1;
varying flat vec2 fcl;
varying flat ivec4 fva;
varying flat ivec4 fvb;
varying flat ivec4 fvc;
varying flat ivec4 fvd;
varying flat ivec4 fve;
uniform bool prev = false;
uniform int anim_n = 0;
uniform ivec2 anim_from[20];
uniform ivec2 anim_to[20];
uniform int wkey[180]; // Q.EXE 0x7f3a8 flags[file * 12 + tile] & 1: 1 = keyed column (index 0 see-through), 0 = opaque column (0x425ec picks 0x83074)
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
ivec2 fspan(int VX[6], int VY[6], int n, int top, int bot, int y){
	int lc = top;
	int li = (top + n - 1) % n;
	for (int t = 0; t < 6; t++){
		if (VY[li] <= y && VY[li] >= VY[lc]){ /* DOS filler 0x4a6e4 switches an edge only when y == its end row: a vertex above the current one is never taken (bottom-row wrap drew 1 stray px, 11-23) */
			lc = li;
			li = (li + n - 1) % n;
		}
		else break;
	}
	int rc = top;
	int ri = (top + 1) % n;
	for (int t = 0; t < 6; t++){
		if (VY[ri] <= y && VY[ri] >= VY[rc]){
			rc = ri;
			ri = (ri + 1) % n;
		}
		else break;
	}
	int dyl = VY[li] - VY[lc];
	int xl = dyl == 0 ? VX[lc] : (VX[lc] * 1024 + (((VX[li] - VX[lc]) * 1024) / dyl) * (y - VY[lc])) >> 10;
	int dyr = VY[ri] - VY[rc];
	int xr = dyr == 0 ? VX[rc] : (VX[rc] * 1024 + (((VX[ri] - VX[rc]) * 1024) / dyr) * (y - VY[rc])) >> 10;
	return ivec2(xl, xr + 1);
}
float sv(float d){
	return clamp(floor(floor(d) * 256.0 / 110.0), 0.0, 4095.0);
}
void vertex(){
	vec4 vp0 = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	float kill = 0.0;
	float ra = floor(COLOR.a * 255.0 + 0.5);
	fq = vec3(mod(ra, 4.0), floor(ra / 4.0), floor(-VERTEX.y / ws + 0.5));
	fc0 = CUSTOM0;
	fc1 = CUSTOM1;
	fcl = COLOR.rg;
	oid = CUSTOM2.x;
	wnt = CUSTOM2.y;
	wtile = UV2;
	if (UV2.y > 14.5){
		float dmin = 1e9;
		float dmax = -1e9;
		for (int k = 0; k < 4; k++){
			vec2 c = k == 0 ? CUSTOM0.xy : (k == 1 ? CUSTOM0.zw : (k == 2 ? CUSTOM1.xy : CUSTOM1.zw));
			float d = -(MODELVIEW_MATRIX * vec4(c.x, VERTEX.y, c.y, 1.0)).z * 16.0;
			dmin = min(dmin, d);
			dmax = max(dmax, d);
		}
		if (dmax < 15.0) kill = 1.0;
		dmin = max(dmin, 15.0);
		dmax = max(dmax, 15.0);
		vec4 ct = PROJECTION_MATRIX * vec4(0.0, vp0.y, -dmax / 16.0, 1.0);
		vec4 cb = PROJECTION_MATRIX * vec4(0.0, vp0.y, -dmin / 16.0, 1.0);
		float yt = floor((0.5 + ct.y / ct.w * 0.5) * 200.0);
		float yb = floor((0.5 + cb.y / cb.w * 0.5) * 200.0);
		float st = sv(dmax);
		float sb = sv(dmin);
		if (yt > yb){
			float t = yt;
			yt = yb;
			yb = t;
			t = st;
			st = sb;
			sb = t;
		}
		sh = vec3(yt, st, yb > yt ? trunc((sb - st) / (yb - yt)) : 0.0);
	}
	else if (doswall){
		int n = int(CUSTOM1.x + 0.5);
		float wq_y = CUSTOM0.y - CUSTOM0.w;
		float wq_x = CUSTOM0.z - CUSTOM0.x;
		int wq_ang = int(floor(degrees(atan(min(abs(wq_x), abs(wq_y)), max(max(abs(wq_x), abs(wq_y)), 0.0001))) + 0.001));
		if (abs(wq_y) > abs(wq_x)) wq_ang = 90 - wq_ang;
		if (wq_x < 0.0) wq_ang = 180 - wq_ang;
		if (wq_y < 0.0) wq_ang = 360 - wq_ang;
		if (wq_ang >= 360) wq_ang -= 360;
		int wq_d = abs(wq_ang - hdeg);
		if (wq_d > 180) wq_d = 360 - wq_d;
		if (wq_d > 120) wq_d = 180 - wq_d;
		int wq_div = max(110 - (wq_d >> 1), 1);
		int kk = int(CUSTOM1.y + 0.5);
		int zt = int(floor(CUSTOM1.z + 0.5));
		int zb = int(floor(CUSTOM1.w + 0.5));
		int camz = -int(floor(INV_VIEW_MATRIX[3].y / ws + 0.5));
		int vx[17];
		int vd[17];
		int sx[17];
		int yt[17];
		int yb[17];
		for (int k = 0; k <= 16; k++){
			if (k > n) break;
			vec2 p = mix(CUSTOM0.zw, CUSTOM0.xy, float(k) / float(n));
			vec4 v = VIEW_MATRIX * vec4(p.x, 0.0, p.y, 1.0);
			vx[k] = int(floor(v.x / ws + 0.5));
			vd[k] = int(floor(-v.z / ws + 0.5));
			if (wtab){
				ivec2 cl = ivec2(floor(COLOR.rg * 255.0 + 0.5));
				ivec2 lp = ivec2(floor(p / ws + 0.5)) - cl * 512;
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
				vx[k] = ((-fcam.y * ti) >> 6) + ((-fcam.x * tj) >> 6) - bcx;
				vd[k] = ((-fcam.x * ti) >> 6) + ((tj * fcam.y) >> 6) - bcy;
			}
		}
		int cnt = n + 1;
		bool kl = false;
		if (vd[0] <= 9 && vd[n] <= 9) kl = true;
		else{
			int s = 0;
			for (int k = 0; k <= 16; k++){
				if (s < cnt && vd[s] < 12) s++;
			}
			if (s == 0){
				int e = cnt - 1;
				for (int k = 0; k <= 16; k++){
					if (e >= 0 && vd[e] < 12) e--;
				}
				if (e != cnt - 1){
					int dd = vd[e] - vd[e + 1];
					if (dd != 0) vx[e + 1] = ((vx[e] - vx[e + 1]) * (12 - vd[e + 1])) / dd + vx[e + 1];
					vd[e + 1] = 12;
					cnt = e + 2;
				}
			}
			else if (s < cnt){
				int dd = vd[s] - vd[s - 1];
				if (dd != 0) vx[s - 1] = ((vx[s] - vx[s - 1]) * (12 - vd[s - 1])) / dd + vx[s - 1];
				vd[s - 1] = 12;
			}
			else kl = true;
		}
		if (!kl){
			for (int k = 0; k <= 16; k++){
				if (k >= cnt) break;
				int dc = max(vd[k], 12);
				sx[k] = (vx[k] * 256) / dc + 160;
				yt[k] = ((zt - camz) * 256) / dc + 100;
				yb[k] = ((zb - camz) * 256) / dc + 100;
			}
			bool rev = sx[cnt - 1] < sx[0];
			if (rev && COLOR.b < 0.75) kl = true;
			if (rev) wtile = CUSTOM2.zw;
			if (kk + 1 > cnt - 1) kl = true;
			if (!kl){
				int f = 0;
				for (int k = 0; k <= 16; k++){
					if (f < cnt){
						int X = sx[rev ? cnt - 1 - f : f];
						if (X < 0 || X > 320) f++;
					}
				}
				if (f >= cnt) kl = true;
				else{
					int l1 = max(f, 1);
					int g = l1;
					for (int k = 0; k <= 16; k++){
						if (g < cnt){
							int X = sx[rev ? cnt - 1 - g : g];
							int XW = ((X + 32768) & 65535) - 32768;
							if (XW >= 0 && (wnt > 0.5 || XW <= 320)) g++;
						}
					}
					if (g >= cnt) g = cnt - 1;
					int r0 = l1 - 1;
					int ka = rev ? cnt - 2 - kk : kk;
					if (ka < r0 || ka + 1 > g) kl = true;
					int i0 = rev ? cnt - 1 - r0 : r0;
					int iN = rev ? cnt - 1 - g : g;
					int dx = sx[iN] - sx[i0];
					if (dx <= 0) kl = true;
					if (!kl){
						int ia = rev ? kk + 1 : kk;
						int ib = rev ? kk : kk + 1;
						int s0 = clamp((vd[rev ? cnt - 1 : 0] * 256) / wq_div, 0, 4095);
						int s1 = clamp((vd[rev ? 0 : cnt - 1] * 256) / wq_div, 0, 4095);
						int ss = (s1 - s0) / dx;
						int tst = ((yt[iN] - yt[i0]) * 1024) / dx;
						int bst = ((yb[iN] - yb[i0]) * 1024) / dx;
						int a0 = 0;
						for (int m = 0; m < 16; m++){
							if (m >= r0 && m < ka){
								int wm = sx[rev ? cnt - 2 - m : m + 1] - sx[rev ? cnt - 1 - m : m];
								if (wm > 0) a0 += wm * (((63 % wm) << 10) / wm);
							}
						}
						wa = ivec4(sx[i0], sx[ia], sx[ib], a0 & 1023);
						wb = ivec4(yt[i0], tst, yb[i0], bst);
						sh = vec3(float(sx[i0]), float(s0), float(ss));
						int cid = int(COLOR.a * 255.0 + 0.5);
						int io = (cid == 1 || cid == 2) ? kk : kk + 1;
						int px = sx[io];
						int py = cid < 2 ? ((yt[i0] * 1024 + 512 + (px - sx[i0]) * tst) >> 10) - 2 : ((yb[i0] * 1024 + 512 + (px - sx[i0]) * bst) >> 10) + 3;
						float dz = float(max(vd[io], 12)) * ws;
						vec2 nd = vec2(float(px) / 160.0 - 1.0, float(py) / 100.0 - 1.0);
						vec3 vv = vec3((dz * nd.x + PROJECTION_MATRIX[2][0] * dz) / PROJECTION_MATRIX[0][0], (dz * nd.y + PROJECTION_MATRIX[2][1] * dz) / PROJECTION_MATRIX[1][1], -dz);
						VERTEX = (inverse(MODELVIEW_MATRIX) * vec4(vv, 1.0)).xyz;
					}
				}
			}
		}
		if (kl) kill = 1.0;
	}
	else{
		vec4 a = MODELVIEW_MATRIX * vec4(CUSTOM0.x, VERTEX.y, CUSTOM0.y, 1.0);
		vec4 b = MODELVIEW_MATRIX * vec4(CUSTOM0.z, VERTEX.y, CUSTOM0.w, 1.0);
		float da = -a.z * 16.0;
		float db = -b.z * 16.0;
		if (da < 12.0 && db < 12.0) kill = 1.0;
		else{
			if (da < 12.0){
				a = mix(a, b, (12.0 - da) / (db - da));
				da = 12.0;
			}
			if (db < 12.0){
				b = mix(b, a, (12.0 - db) / (da - db));
				db = 12.0;
			}
		}
		vec4 ca = PROJECTION_MATRIX * a;
		vec4 cb = PROJECTION_MATRIX * b;
		float xa = floor((ca.x / ca.w * 0.5 + 0.5) * 320.0);
		float xb = floor((cb.x / cb.w * 0.5 + 0.5) * 320.0);
		float sa = sv(da);
		float sb = sv(db);
		if (xa > xb){
			float t = xa;
			xa = xb;
			xb = t;
			t = sa;
			sa = sb;
			sb = t;
		}
		sh = vec3(xa, sa, xb > xa ? trunc((sb - sa) / (xb - xa)) : 0.0);
	}
	if (UV2.y > 14.5 && dosfloor){
		int z = int(fq.z) - fcamz;
		ivec2 cl = ivec2(floor(COLOR.rg * 255.0 + 0.5));
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
		int PX[4];
		int PD[4];
		vec2 QQ[4];
		int ci = 0;
		float bd = 1e9;
		for (int k = 0; k < 4; k++){
			vec2 p = k == 0 ? CUSTOM0.xy : (k == 1 ? CUSTOM0.zw : (k == 2 ? CUSTOM1.xy : CUSTOM1.zw));
			float dd = distance(p, VERTEX.xz);
			if (dd < bd){
				bd = dd;
				ci = k;
			}
			QQ[k] = (p - CUSTOM0.xy) / ws;
			ivec2 lp = ivec2(floor(p / ws + 0.5)) - cl * 512;
			int ti = lp.x >> 5;
			int tj = lp.y >> 5;
			PX[k] = ((-fcam.y * ti) >> 6) + ((-fcam.x * tj) >> 6) - bcx;
			PD[k] = ((-fcam.x * ti) >> 6) + ((tj * fcam.y) >> 6) - bcy;
		}
		float ar = 0.0;
		for (int k = 0; k < 4; k++){
			vec2 a = QQ[k];
			vec2 b = QQ[(k + 1) & 3];
			ar += a.x * b.y - b.x * a.y;
		}
		int CX[6];
		int CD[6];
		int n = 0;
		for (int k = 0; k < 4; k++){
			int pk = (k + 3) & 3;
			int nk = (k + 1) & 3;
			if (PD[k] >= 15){
				CX[n] = PX[k];
				CD[n] = PD[k];
				n++;
			}
			else{
				if (PD[pk] >= 15){
					CX[n] = ((15 - PD[k]) * (PX[pk] - PX[k])) / (PD[pk] - PD[k]) + PX[k];
					CD[n] = 15;
					n++;
				}
				if (PD[nk] >= 15){
					CX[n] = ((15 - PD[k]) * (PX[nk] - PX[k])) / (PD[nk] - PD[k]) + PX[k];
					CD[n] = 15;
					n++;
				}
			}
		}
		bool fk = n < 3 || z == 0 || !((z > 0 && ar * fsign > 0.0) || (z < 0 && ar * fsign < 0.0));
		int VX[6];
		int VY[6];
		int VS[6];
		int top = 0;
		int bot = 0;
		int mnx = 1000000;
		int mxx = -1000000;
		if (!fk){
			for (int k = 0; k < n; k++){
				VX[k] = (CX[k] * 256) / CD[k] + 160;
				VY[k] = (z * 256) / CD[k] + 100;
				VS[k] = clamp((CD[k] * 256) / 110, 0, 4095);
				if (VY[k] <= VY[top]) top = k;
				if (VY[k] >= VY[bot]) bot = k;
				mnx = min(mnx, VX[k]);
				mxx = max(mxx, VX[k]);
			}
			if (!(VY[top] < VY[bot] && 37 < VY[bot] && VY[top] <= 149)) fk = true;
		}
		if (!fk){
			int x0 = clamp(mnx, 0, 320);
			int x1 = clamp(mxx + 1, 0, 320);
			int y0 = clamp(VY[top], 37, 150);
			int y1 = clamp(VY[bot] + 1, 37, 150);
			if (x1 <= x0 || y1 <= y0) fk = true;
			else{
				for (int k = n; k < 6; k++){
					VX[k] = 0;
					VY[k] = 0;
				}
				fva = ivec4(VX[0], VX[1], VX[2], VX[3]);
				fvb = ivec4(VY[0], VY[1], VY[2], VY[3]);
				fvc = ivec4(VX[4], VX[5], VY[4], VY[5]);
				fvd = ivec4(n, top, bot, 0);
				fve = ivec4(VS[top], (VS[bot] - VS[top]) / (VY[bot] - VY[top]), cdx * cdx + cdy * cdy, 0);
				float px = (ci == 0 || ci == 3) ? float(x0) : float(x1);
				float py = ci < 2 ? float(y0) : float(y1);
				POSITION = vec4(px / 160.0 - 1.0, (py - float(frow)) / 100.0 - 1.0, 0.0, 1.0);
			}
		}
		if (fk) kill = 1.0;
	}
	if (!(UV2.y > 14.5 && dosfloor) || kill > 0.5) POSITION = PROJECTION_MATRIX * (MODELVIEW_MATRIX * vec4(VERTEX, 1.0));
	vec2 dc = abs(round(COLOR.rg * 255.0) - cam_cell);
	far = (cam_cell.x > -50.0 && max(dc.x, dc.y) > 3.5) ? 1.0 : 0.0;
	if (kill > 0.5) far = 1.0;
}
void fragment(){
	if (far > 0.5) discard;
	DEPTH = FRAGCOORD.z;
	bool dw = doswall && UV2.y < 14.5;
	vec2 ac = UV2.y > 14.5 ? UV2 : wtile;
	for (int ak = 0; ak < anim_n; ak++){
		if (ivec2(ac + 0.5) == anim_from[ak]){
			ac = vec2(anim_to[ak]);
			break;
		}
	}
	if (!dw && abs(COLOR.b - 0.5) < 0.1 && FRONT_FACING == cullflip) discard;
	float i;
	float flv = -1.0;
	if (UV2.y > 14.5 && dosfloor){
		int y = int(floor(SCREEN_UV.y * 200.0)) + frow;
		int x = int(floor(SCREEN_UV.x * 320.0));
		int z = int(floor(fq.z + 0.5)) - fcamz;
		int n = fvd.x;
		int top = fvd.y;
		int bot = fvd.z;
		int VX[6];
		int VY[6];
		VX[0] = fva.x;
		VX[1] = fva.y;
		VX[2] = fva.z;
		VX[3] = fva.w;
		VX[4] = fvc.x;
		VX[5] = fvc.y;
		VY[0] = fvb.x;
		VY[1] = fvb.y;
		VY[2] = fvb.z;
		VY[3] = fvb.w;
		VY[4] = fvc.z;
		VY[5] = fvc.w;
		if (y < max(VY[top], 37) || y > min(VY[bot], 149) || y == 100) discard;
		ivec2 sp = fspan(VX, VY, n, top, bot, y);
		int xl = sp.x;
		if (x < xl || x >= min(sp.y, 320)) discard;
		xl = max(xl, 0);
		int pry = -1000;
		for (int t = 1; t <= 112; t++){
			int c = y - t;
			if (c < VY[top] || c < 37) break;
			if (c == 100) continue;
			ivec2 s2 = fspan(VX, VY, n, top, bot, c);
			if (s2.y > 0 && s2.x < 320 && min(s2.y, 320) > max(s2.x, 0)){
				pry = c;
				break;
			}
		}
		float fdz = float(z * 256) / float(y - 100) * ws;
		vec4 fcp = PROJECTION_MATRIX * vec4(0.0, 0.0, -fdz, 1.0);
		DEPTH = fdsw ? 1.0 - fcp.z / fcp.w : fcp.z / fcp.w * (1.0 - 1e-5 * float(min(fve.z, 200)));
		int du = 0;
		int dv = 0;
		int ub = fcam.x;
		int vb = fcam.y;
		int pdu = 0;
		int pdv = 0;
		int p6 = int(floor(fq.y + 0.5));
		int s9 = p6 + 9;
		int ls = 10 - p6;
		int rt = int(floor(fq.x + 0.5));
		for (int ps = 0; ps < 2; ps++){
			int yy = ps == 0 ? pry : y;
			if (ps == 0 && pry == -1000) continue;
			int k = yy - 100;
			int tb = k >= 1 ? 5120 / (5120 / k) : -(5120 / (5120 / (1 - k)));
			int q = (z * 256) / tb;
			int a = fcam.x * q;
			int b = q * fcam.y;
			int tdu;
			int tdv;
			int tub;
			int tvb;
			if (rt == 0){
				tdu = (-b) >> s9;
				tdv = (-a) >> s9;
				tub = (-((a >> 11) - fcam.z)) << ls;
				tvb = ((b >> 11) + fcam.w) << ls;
			}
			else if (rt == 1){
				tdv = b >> s9;
				tdu = (-a) >> s9;
				tvb = ((a >> 11) - fcam.z) << ls;
				tub = ((b >> 11) + fcam.w) << ls;
			}
			else if (rt == 2){
				tdu = b >> s9;
				tdv = a >> s9;
				tub = ((a >> 11) - fcam.z) << ls;
				tvb = (-((b >> 11) + fcam.w)) << ls;
			}
			else{
				tdv = (-b) >> s9;
				tdu = a >> s9;
				tvb = (-((a >> 11) - fcam.z)) << ls;
				tub = (-((b >> 11) + fcam.w)) << ls;
			}
			if (ps == 0){
				pdu = tdu;
				pdv = tdv;
				ub = tub;
				vb = tvb;
			}
			else{
				du = tdu;
				dv = tdv;
			}
		}
		int kx = xl - 160;
		uint u0 = uint(ub + (pdu & 65535) * kx) & 65535u;
		uint v0 = uint(vb + ((kx * pdv) & 65535)) & 65535u;
		uint e = (u0 * 65536u + v0) + uint(max(0, x - xl - 1)) * (uint(du & 65535) * 65536u + uint(dv & 65535));
		int uu = int(e / 65536u);
		int vv = int(e & 65535u);
		i = floor(texelFetch(tex, ivec2(int(floor(UV2.x + 0.5)) * 64 + ((uu >> 10) & 63), 960 + ((vv >> 10) & 63)), 0).r * 255.0 + 0.5);
		flv = float(fve.x + fve.y * (y - VY[top]));
	}
	else if (dw){
		int x = int(floor(SCREEN_UV.x * 320.0));
		int y = int(floor(SCREEN_UV.y * 200.0));
		if (x < wa.y || x >= wa.z) discard;
		int col = x - wa.x;
		int top = (wb.x * 1024 + 512 + col * wb.y) >> 10;
		int bot = ((wb.z * 1024 + 512 + col * wb.w) >> 10) + 1;
		if (y < top || y >= bot || y >= 149) discard;
		int h = bot - top;
		int tb = h < 3 ? 65535 : 131072 / h;
		int vv = min(((tb >> 1) * (y - top)) >> 10, 63);
		int w = wa.z - wa.y;
		int j = x - wa.y;
		int uu = min(j * (63 / w) + ((wa.w + j * (((63 % w) << 10) / w)) >> 10), 63);
		i = floor(texelFetch(tex, ivec2(int(ac.x + 0.5) * 64 + uu, int(ac.y + 0.5) * 64 + vv), 0).r * 255.0 + 0.5);
	}
	else{
		vec2 u = clamp(fract(UV), 0.008, 0.992);
		i = floor(texture(tex, (ac + u) / 16.0).r * 255.0 + 0.5);
	}
	if (i < 0.5 && UV2.y < 14.5 && (prev || (wkey[clamp(int(ac.y + 0.5), 0, 14) * 12 + clamp(int(ac.x + 0.5), 0, 11)] & (wnt > 0.5 ? 255 : 1)) != 0)) discard;
	float c = UV2.y > 14.5 ? floor(SCREEN_UV.y * 200.0) : floor(SCREEN_UV.x * 320.0);
	ALBEDO = shadedlv(i, flv >= 0.0 ? flv : sh.y + sh.z * (c - sh.x));
	if (painter && cam_cell.x > -50.0){
		ivec2 oc = ivec2(floor(fcl * 255.0 + 0.5)) - ivec2(cam_cell);
		DEPTH = (texelFetch(ordt, ivec2(int(oid + 0.5), (oc.y + 3) * 7 + oc.x + 3), 0).r + 1.0) / 8192.0;
		if (DEPTH <= 0.0) discard;
		DEPTH += 0.5;
		if (idv) ALBEDO = vec3((oid + 8.0) / 63.0, float((oc.y + 3) * 7 + oc.x + 11) / 63.0, UV2.y > 14.5 ? 0.5 : 0.0);
		if (kil == ivec2((oc.y + 3) * 7 + oc.x + 3, int(oid + 0.5))) discard;
	}
}
