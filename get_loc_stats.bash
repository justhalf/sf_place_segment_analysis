# 05 Nov 2018
# By: Aldrian Obaja Muis
# To print location statistics

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
        --ltf_dir ${lang}/setE/IL/ltf \
        --json_in ${lang}/setE/IL/sf_anno/gold_sf_IL.json \
        --mention_dir ${lang}/setE/IL/sf_anno/mentions \
        --out_file loc_stats_${lang}.log \
        ${ignore_doc_no_sf_opt}
done
