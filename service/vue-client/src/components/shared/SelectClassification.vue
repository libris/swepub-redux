<script>
import SelectBase from '@/components/shared/SelectBase';

export default {
  name: 'select-classification',
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
  },
  methods: {
    transformOptions(classifications) {
      const sortedClassifications = [];
      const lang = this.settings.language;

      function addClassification(key, value) {
        sortedClassifications.push({ label: `${key} - ${value[lang]}`, id: key });
      }

      function traverseSubcats(obj) {
        Object.keys(obj).forEach((key) => {
          if (key !== 'statusCode') {
            addClassification(key, obj[key]);
          }
          if (obj[key].hasOwnProperty('subcategories')) {
            traverseSubcats(obj[key].subcategories);
          }
        });
      }

      traverseSubcats(classifications);
      return sortedClassifications;
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
