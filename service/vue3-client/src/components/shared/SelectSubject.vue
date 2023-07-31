<script>
import SelectBase from '@/components/shared/SelectBase.vue';
import { useSettingsStore } from '@/stores/settings';
import { mapState } from 'pinia';

export default {
  name: 'select-subject',
  extends: SelectBase,
  components: {},
  props: {},
  data() {
    return {
      label: 'Forskningsämne (SSIF)',
      fetchMsg: 'Hittade inga forskningsämnen',
      valueProp: 'id',
      labelProp: 'label',
      apiEndpoint: '/info/research-subjects',
    };
  },
  computed: {
    ...mapState(useSettingsStore, ['language']),
  },
  methods: {
    transformOptions(subjects) {
      const sortedSubjects = [];
      const lang = this.language;

      function addSubject(key, value) {
        sortedSubjects.push({ label: `${key} - ${value[lang]}`, id: key });
      }

      function traverseSubcats(obj) {
        Object.keys(obj).forEach((key) => {
          if (key !== 'statusCode') {
            addSubject(key, obj[key]);
          }
          if (obj[key].hasOwnProperty('subcategories')) {
            traverseSubcats(obj[key].subcategories);
          }
        });
      }

      traverseSubcats(subjects);
      return sortedSubjects;
    },
  },
  mounted() {
  },
  watch: {
  },
};
</script>

<style lang="scss">
:root {
}
</style>
