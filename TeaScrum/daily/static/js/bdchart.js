function get_context(canvas_id){
	if (!Modernizr.canvas){
		alert('Your browser does not support HTML5 Canvas');
		return null;
	}
	var b_canvas = document.getElementById(canvas_id);
	return b_canvas.getContext('2d');
}
function set_line_style(ctx,style) {
	var ss = ctx.strokeStyle, lw = ctx.lineWidth;
	ctx.strokeStyle = style.color;
	ctx.lineWidth = style.width;
	ctx.beginPath();
	return {color: ss, width: lw};
}
function set_font_style(ctx, style){
	var ofont = ctx.font, obaseline = ctx.textBaseline, oalign = ctx.textAlign;
	ctx.font = style.font;
	ctx.textBaseline = style.base;
	ctx.textAlign = style.align;
	return {font: ofont, base: obaseline, align: oalign};
}
function draw_x(ctx, x0, y0, step, xpts) {
	var yd = 10;
	set_line_style(ctx, {color:'#000', width:2});
	set_font_style(ctx, {font:'bold 12px san-serif',base:'top',align:'left'});
	ctx.moveTo(x0, y0 - yd);
	ctx.lineTo(x0, y0);
	for (var x=x0, i=0; i<xpts.length;x+=step,i++) {
		ctx.moveTo(x, y0 - yd);
		ctx.lineTo(x, y0);
		ctx.lineTo(x + step, y0);
		ctx.fillText(xpts[i][0]+'-'+xpts[i][1], x, y0);
	}
	ctx.stroke();
}
function draw_y(ctx, x0, y0, step, pts, w, d) {
	set_line_style(ctx, {color:'#000', width:2});
	set_font_style(ctx, {font:'bold 12px san-serif',base:'top',align:'right'});
	ctx.moveTo(x0, y0);
	ctx.lineTo(x0, 0);
	ctx.stroke();
	set_line_style(ctx, {color:'#ccc', width:1});
	var l = 1;
	for (var y=y0-step, i=0; i<pts; y-=step, i++) {
		ctx.moveTo(x0, y);
		ctx.lineTo(w, y);
		ctx.fillText(l, x0-2, y-6);
		l ++;
	}
	ctx.stroke();
}
function draw_d(ctx, x0, y0, xstep, aheight, maxy, xpts) {
	var x = x0, y = y0;
	set_line_style(ctx, {color:'#00F', width:4});
	ctx.moveTo(x, y);
	for (var i=1; i<xpts.length; i++) {
		if (xpts[i][2] < 0) break;
		x += xstep;
		y = aheight - xpts[i][2] * aheight / maxy;
		ctx.lineTo(x, y);
	}
	ctx.stroke();
}
/**
 * Draw BurnDown chart for the input dataset. 
 * @param int maxy max Y 
 * @param Array xpts [[month,day,Y],..]
 */
function draw_burndown_chart(canvas_id, maxy, xpts) {
	var ctx = get_context(canvas_id);
	var lmargin = 40, awidth = ctx.canvas.width - lmargin, bmargin = 20, aheight = ctx.canvas.height - bmargin;
	var xstep = awidth / xpts.length, ystep = aheight / maxy;
	draw_x(ctx, lmargin, aheight, xstep, xpts);
	draw_y(ctx, lmargin, aheight, ystep, maxy, ctx.canvas.width, aheight / maxy);
	//draw diagonal line
	var ostyle = set_line_style(ctx,{color:'#F00',width:1});
	ctx.moveTo(lmargin, 0); ctx.lineTo(ctx.canvas.width-xstep, aheight);
	ctx.stroke(true);
	set_line_style(ctx, ostyle);
	draw_d(ctx, lmargin, 0, xstep, aheight, maxy, xpts);
}
