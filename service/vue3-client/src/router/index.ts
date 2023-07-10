import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/bibliometrics',
    },
    {
      path: '/classify/:section?',
      name: 'Classify',
      meta: { title: 'Ämnesklassificering' },
      component: () => import('../views/Classify.vue'),
    },
    {
      path: '/bibliometrics/:section?',
      name: 'Bibliometrics',
      meta: { title: 'Bibliometri' },
      props: (route) => ({ query: route.query }),
      component: () => import('../views/Bibliometrics.vue'),
    },
    {
      path: '/process/:source?/:service?/:subservice?', // ? = optional param
      name: 'Process',
      meta: { title: 'Databearbetning' },
      props: (route) => ({ query: route.query, params: route.params }),
      component: () => import('../views/Process.vue'),
    },
    {
      path: '/datastatus/:source?',
      name: 'Datastatus',
      meta: { title: 'Datastatus' },
      props: (route) => ({ params: route.params, query: route.query }),
      component: () => import('../views/Datastatus.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      meta: { title: 'Sidan kan inte hittas' },
      component: () => import('../views/NotFound.vue'),
    },
  ]
})

export default router
