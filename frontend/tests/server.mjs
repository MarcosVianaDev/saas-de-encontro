import { createServer } from 'vite';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
for (const [port, mode] of [[18081,'django'],[18082,'mock']]) {
  const server=await createServer({configFile:false,root,cacheDir:fileURLToPath(new URL('../../.tools/vite-browser-'+mode+'/',import.meta.url)),define:{'import.meta.env.VITE_FRONTEND_DATA_MODE':JSON.stringify(mode)},server:{host:'127.0.0.1',port,strictPort:true,proxy:{'/ws/':{target:'ws://127.0.0.1:18080',ws:true},'/api/':'http://127.0.0.1:18080','/admin/':'http://127.0.0.1:18080','/mcx/':'http://127.0.0.1:18080','/static/':'http://127.0.0.1:18080'}}});
  await server.listen();
  console.log(`Test frontend ready: ${port} (${mode})`);
}
