<script>
import SelectBase from '@/components/shared/SelectBase';

export default {
  name: 'select-source',
  extends: SelectBase,
  components: {
  },
  props: {
  },
  data() {
    return {
      label: 'Organisation',
      fetchMsg: 'Hittade inga organisationer',
      valueProp: 'code',
      labelProp: 'name',
    };
  },
  computed: {
    apiEndpoint() {
      // sources sent from parent in datastatus
      if (!this.providedOptions) {
        return '/info/sources';
      } return null;
    },
  },
  methods: {
    transformOptions(response) {
      const { sources } = response;
      if (sources && sources.length > 0) {
        return sources.slice().sort((a, b) => a.name.toLowerCase()
          .localeCompare(b.name.toLowerCase()));
      }
      return sources;
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
