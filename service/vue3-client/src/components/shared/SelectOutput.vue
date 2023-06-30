<script>
import SelectBase from '@/components/shared/SelectBase.vue';
import { useSettingsStore } from '@/stores/settings';
import { mapState } from 'pinia';

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
    ...mapState(useSettingsStore, ['language']),
  },
  methods: {
    transformOptions(types) {
      delete types.statusCode;
      const transformedOptions = [];
      Object.keys(types).forEach((type) => {
        if (types[type].hasOwnProperty('subcategories')) {
          transformedOptions.push({
            label: `${types[type][this.language].toUpperCase()} - ALLA`,
            value: `*${type}`,
            sortKey: `${types[type][this.language].toUpperCase()} - ALLA`,
          }); // add broader option - '*' is just to track these internally
          transformedOptions.push({ // level 1
            label: `${types[type][this.language]}`,
            value: type,
            sortKey: `${types[type][this.language].toUpperCase()} - ALLA`,
          });
          Object.keys(types[type].subcategories).forEach((subtype) => { // level 2
            transformedOptions.push({
              label: `-- ${types[type].subcategories[subtype][this.language]}`,
              value: `${type}.${subtype}`,
              sortKey: `${types[type][this.language].toUpperCase()} - ALLA - ${types[type].subcategories[subtype][this.language]}`,
            });
          });
        } else {
          transformedOptions.push({ // level 1 - no subcats
            label: types[type][this.language],
            value: type,
            sortKey: types[type][this.language],
          });
        }
      });
      transformedOptions.sort((a, b) => a.sortKey.toLowerCase()
        .localeCompare(b.sortKey.toLowerCase(), 'sv'));
      // For whatever reason we need to remove `sortKey` from each option
      // before returning, because otherwise Vue code elsewhere gets confused
      // or angry or something. Sigh.
      return transformedOptions.map(({ sortKey, ...item }) => item);
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
