<script>
export default {
  name: 'validation-mixin',
  components: {
  },
  props: {
  },
  data() {
    return {};
  },
  computed: {
    yearInputError() {
      const { from, to } = this.selected.years;

      if (this.selected.years.to && !this.selected.years.from) {
        return '"Från och med" måste fyllas i';
      }
      if (this.selected.years.from && !this.selected.years.to) {
        return '"Till och med" måste fyllas i';
      }
      if (from.toString().length !== 4 || to.toString().length !== 4) {
        if (!from && !to) {
          return false;
        }
        return 'Årtal måste anges med fyra siffror';
      }
      if (parseInt(from) > parseInt(to)) {
        return '"Från och med" kan inte vara senare än "till och med"';
      }
      return false;
    },
  },
  methods: {
  },
  mounted() {
  },
  watch: {
  },
};
</script>
