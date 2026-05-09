import { useState } from 'react'
import { I18nProvider } from './i18n'
import LandingPage from './pages/LandingPage'
import Dashboard from './pages/Dashboard'
import ProviderForm from './pages/ProviderForm'
import SettingsPage from './pages/SettingsPage'

function App() {
  const [page, setPage] = useState('landing')
  const [editingProvider, setEditingProvider] = useState(null)

  const navigate = (target, provider = null) => {
    setEditingProvider(provider)
    setPage(target)
  }

  return (
    <I18nProvider>
      {(() => {
        switch (page) {
          case 'landing':
            return <LandingPage onGetStarted={() => navigate('dashboard')} />
          case 'dashboard':
            return <Dashboard onNavigate={navigate} />
          case 'provider-form':
            return <ProviderForm provider={editingProvider} onBack={() => navigate('dashboard')} />
          case 'settings':
            return <SettingsPage onBack={() => navigate('dashboard')} />
          default:
            return <LandingPage onGetStarted={() => navigate('dashboard')} />
        }
      })()}
    </I18nProvider>
  )
}

export default App
