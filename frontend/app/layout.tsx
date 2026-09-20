import './styles.css';
import 'mapbox-gl/dist/mapbox-gl.css';
import {ServiceWorker} from './service-worker';
import {QueueStatus} from './queue-status';
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body><ServiceWorker/><QueueStatus/>{children}</body></html>}
