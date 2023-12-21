#include "ItemTranslator.h"

namespace synthesis {

    ItemTranslator::ItemTranslator() : num_items(0) {
        // left intentionally blank
    }

    ItemTranslator::ItemTranslator(uint64_t num_items) : num_items(num_items) {
        item_to_translation.resize(num_items, num_items);
    }

    void ItemTranslator::clear() {
        num_items = 0;
        item_to_translation.clear();
        translation_to_item.clear();
    }

    void ItemTranslator::resize(uint64_t num_items) {
        item_to_translation.resize(num_items, num_items);
    }

    uint64_t ItemTranslator::numTranslations() const {
        return translation_to_item.size();
    }

    bool ItemTranslator::hasTranslation(uint64_t item) const {
        return item_to_translation[item] != num_items;
    }

    uint64_t ItemTranslator::translate(uint64_t item) {
        uint64_t *translation = &(item_to_translation[item]);
        if(*translation == num_items) {
            *translation = numTranslations();
            translation_to_item.push_back(item);
        }
        return *translation;
    }

    uint64_t ItemTranslator::retrieve(uint64_t translation) const {
        return translation_to_item[translation];
    }

    std::vector<uint64_t> const& ItemTranslator::translationToItem() const {
        return translation_to_item;
    }

}