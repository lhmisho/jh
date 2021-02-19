// quick fix for https://github.com/JedWatson/react-select/issues/2651
module.exports = function reactSelectLoader (source) {
    return source
        .replace(' _this$scrollTarget = _this.scrollTarget,', ' _this$scrollTarget = event.currentTarget,')
        .replace(' target = _this.scrollTarget;', ' target = event.currentTarget;');
};