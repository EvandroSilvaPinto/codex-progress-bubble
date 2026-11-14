import qrcode from './vendor/qrcode.mjs';
export function matrixFor(url) {
  const qr=qrcode(0,'M');qr.addData(url,'Byte');qr.make();
  return Array.from({length:qr.getModuleCount()},(_,y)=>Array.from({length:qr.getModuleCount()},(_,x)=>qr.isDark(y,x)));
}
export function paintQR(canvas,url) {
  const matrix=matrixFor(url),scale=8,size=(matrix.length+8)*scale;
  canvas.width=canvas.height=size;
  const context=canvas.getContext('2d');context.fillStyle='#fff';context.fillRect(0,0,size,size);context.fillStyle='#000';
  matrix.forEach((row,y)=>row.forEach((dark,x)=>{if(dark)context.fillRect((x+4)*scale,(y+4)*scale,scale,scale);}));
}
