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
          transformedOptions.push({ label: `${types[type][this.settings.language].toUpperCase()} - ALLA`, value: `*${type}` }); // add broader option - '*' is just to track these internally
          transformedOptions.push({ label: `${types[type][this.settings.language]}`, value: type }); // level 1
          Object.keys(types[type].subcategories).forEach((subtype) => {
            transformedOptions.push({ label: `${types[type].subcategories[subtype][this.settings.language]}`, value: `${type}.${subtype}` }); // level 2
          });
        } else {
          transformedOptions.push({ // level 1 - no subcats
            label: types[type][this.settings.language],
            value: type,
          });
        }
      });
      return transformedOptions;
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
