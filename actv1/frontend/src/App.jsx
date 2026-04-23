import MapView from './components/MapView'
import SidePanel from './components/SidePanel'
import './App.css'

function App() {
  return (
    <div className="app-shell">
      <main className="map-pane">
        <MapView />
      </main>
      <aside className="panel-pane">
        <SidePanel />
      </aside>
    </div>
  )
}

export default App