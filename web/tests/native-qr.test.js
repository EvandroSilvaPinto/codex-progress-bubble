import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {inflateSync} from 'node:zlib';
import jsQR from 'jsqr';

test('desktop PNG independently decodes to the exact private reader URL',()=>{
 const url='https://progress-bubble-mobile.dev-evandrosilvapinto.workers.dev/#'+'a'.repeat(32)+'.'+'b'.repeat(43);
 const script="import sys,base64;sys.path.insert(0,'skills/progress-bubble/scripts');from native_qr import qr_png;print(base64.b64encode(qr_png(sys.argv[1],int(sys.argv[2]))).decode())";
 for(const size of [153,180,216,270,360]){
 const result=spawnSync(process.platform==='win32'?'python':'python3',['-c',script,url,String(size)],{cwd:new URL('../..',import.meta.url),encoding:'utf8'});
 assert.equal(result.status,0,result.stderr);
 const png=Buffer.from(result.stdout.trim(),'base64'),width=png.readUInt32BE(16),height=png.readUInt32BE(20),chunks=[];
 for(let pos=8;pos<png.length;){const length=png.readUInt32BE(pos);if(png.toString('ascii',pos+4,pos+8)==='IDAT')chunks.push(png.subarray(pos+8,pos+8+length));pos+=12+length;}
 const raw=inflateSync(Buffer.concat(chunks)),rgba=new Uint8ClampedArray(width*height*4);
 for(let y=0;y<height;y++){assert.equal(raw[y*(width+1)],0);for(let x=0;x<width;x++){const i=(y*width+x)*4;rgba[i]=rgba[i+1]=rgba[i+2]=raw[y*(width+1)+1+x];rgba[i+3]=255;}}
 assert.equal(jsQR(rgba,width,height)?.data,url,'QR available size '+size);
 }
});
