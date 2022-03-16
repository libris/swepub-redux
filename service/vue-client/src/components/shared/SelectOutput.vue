<script>
import { mapGetters } from 'vuex';
import SelectBase from '@/components/shared/SelectBase';

export default {
  name: 'select-output',
  extends: SelectBase,
  components: {
  },
  props: {
  },
  data() {
    return {
      label: 'Outputtyp',
      fetchMsg: 'Hittade inga outputtyper',
      valueProp: 'value',
      labelProp: 'label',
      apiEndpoint: '/info/output-types',
    };
  },
  computed: {
    ...mapGetters([
      'settings',
    ]),
  },
  methods: {
    transformOptions(types) {
      delete types.statusCode;
      const transformedOptions = [];
      Object.keys(types).forEach((type) => {
        if (types[type].hasOwnProperty('subcategories')) {
          transformedOptions.push({
            label: `${types[type][this.settings.language].toUpperCase()} - ALLA`,
            value: `*${type}`,
            sortKey: `${types[type][this.settings.language].toUpperCase()} - ALLA`,
          }); // add broader option - '*' is just to track these internally
          transformedOptions.push({ // level 1
            label: `${types[type][this.settings.language]}`,
            value: type,
            sortKey: `${types[type][this.settings.language].toUpperCase()} - ALLA`,
          });
          Object.keys(types[type].subcategories).forEach((subtype) => { // level 2
            transformedOptions.push({
              label: `-- ${types[type].subcategories[subtype][this.settings.language]}`,
              value: `${type}.${subtype}`,
              sortKey: `${types[type][this.settings.language].toUpperCase()} - ALLA - ${types[type].subcategories[subtype][this.settings.language]}`,
            });
          });
        } else {
          transformedOptions.push({ // level 1 - no subcats
            label: types[type][this.settings.language],
            value: type,
            sortKey: types[type][this.settings.language],
          });
        }
      });
      return transformedOptions.sort((a, b) => a.sortKey.toLowerCase()
        .localeCompare(b.sortKey.toLowerCase(), 'sv'));
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
