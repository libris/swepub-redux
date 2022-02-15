import Vue from 'vue';
import Router from 'vue-router';

Vue.use(Router);

export default new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      redirect: '/bibliometrics',
    },
    {
      path: '/classify/:section?',
      name: 'Classify',
      meta: { title: 'Ämnesklassificering' },
      component: () => import(/* webpackChunkName: "classify" */'@/views/Classify'),
    },
    {
      path: '/bibliometrics/:section?',
      name: 'Bibliometrics',
      meta: { title: 'Bibliometri' },
      props: (route) => ({ query: route.query }),
      component: () => import(/* webpackChunkName: "bibliometrics" */'@/views/Bibliometrics'),
    },
    {
      path: '/process/:source?/:service?/:subservice?', // ? = optional param
      name: 'Process',
      meta: { title: 'Databearbetning' },
      props: (route) => ({ query: route.query, params: route.params }),
      component: () => import(/* webpackChunkName: "process" */'@/views/Process'),
    },
    {
      path: '/datastatus/:source?',
      name: 'Datastatus',
      meta: { title: 'Datastatus' },
      props: (route) => ({ params: route.params, query: route.query }),
      component: () => import(/* webpackChunkName: "process" */'@/views/Datastatus'),
    },
    {
      path: '*',
      name: 'NotFound',
      meta: { title: 'Sidan kan inte hittas' },
      component: () => import(/* webpackChunkName: "notfound" */'@/views/NotFound'),
    },
  ],
});
