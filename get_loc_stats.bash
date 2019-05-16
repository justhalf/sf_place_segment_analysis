# 05 Nov 2018
# By: Aldrian Obaja Muis
# To print location statistics
# This requires the LTF files to be put under ../../data/{IL5,IL6,IL9,IL10}/setE/IL/ltf
# This requires the SF annotations to be put under ../../data/{IL5,IL6,IL9,IL10}/setE/IL/sf_anno
# This requires the entity mentions to be put under ../../data/{IL5,IL6,IL9,IL10}/setE/IL/mentions
# Adjust the path accordingly for different locations of the data

for lang in "IL5" "IL6" "IL9" "IL10"; do
    if [ "${lang}" == "IL9" ] || [ "${lang}" == "IL10" ]; then
        ignore_doc_no_sf_opt="--ignore_doc_no_sf"
    else
        ignore_doc_no_sf_opt=""
    fi
    lang_code=$(echo ${lang} | tr 'A-Z' 'a-z')
    echo "Language: ${lang}"
    echo "setE"
    python3 get_loc_stats.py \
        --ltf_dir ../../data/langpacks/${lang}/setE/IL/ltf \
        --sf_anno ../../data/langpacks/${lang}/setE/IL/sf_anno \
        --mention_dir ../../data/langpacks/${lang}/setE/IL/sf_anno/mentions \
        --out_file loc_stats_${lang}.log \
        --lang ${lang} \
        ${ignore_doc_no_sf_opt}
done
