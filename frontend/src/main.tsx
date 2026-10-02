import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { toast } from 'sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from '@/components/ui/sonner'
import { EventosProvider } from '@/hooks/eventos'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (e, q) => {
      // só avisa de falhas em consultas que já tinham dado certo (evita spam com a API offline)
      if (q.state.data !== undefined) toast.error(e.message)
    },
  }),
  mutationCache: new MutationCache({ onError: (e) => toast.error(e.message) }),
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: true } },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <EventosProvider>
          <App />
        </EventosProvider>
        <Toaster theme="dark" position="bottom-right" mobileOffset={{ bottom: 84 }} />
      </TooltipProvider>
    </QueryClientProvider>
  </StrictMode>,
)
