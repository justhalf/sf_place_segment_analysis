# SF Description vs SF Place location in the document
Summarizes the analysis of SF Place and its relation to the location of the SF description in the text.

The idea is to analyze whether the mentions of SF place occur near or far away from the sentence (segment) describing the SF.

## Methodology
First, we need to find out the sentence describing the SFs. For this, we use the `description` field in the SF annotations
as a proxy for which sentence describes the SFs. We searched for the text in the `description` field in the actual document, 
and assign the corresponding segment ID to the SFs as the sentence describing/triggering the SFs.

Next, for each SF that has been assigned an entity as its location (SF Place), we find all mentions of that entity in the document
and find the closest mention to the sentence containing the SF description. Then we plot the segment ID of the SF description
versus the segment ID of the closest location mention in Figure 1.

<figure>
  <div>
    <img src="/loc_stats_IL5.png" width="45%"/>
    <img src="/loc_stats_IL6.png" width="45%"/>
  </div>
  <div>
    <img src="/loc_stats_IL9.png" width="45%"/>
    <img src="/loc_stats_IL10.png" width="45%"/>
  </div>
  <p align="center">
    <strong>Figure 1.</strong>
    The plot of segment ID containing the SF description field vs the segment ID containing the closest mention of the corresponding
    SF place in the gold annotations. The black identity line shows where the dots would be if the place mention is found in the same
    segment as the SF description.
  </p>
</figure>

As we can see, most of the location mention of the SFs lie closely to the diagonal, which means they are very likely to be found in
the same sentence. Since this plot does not actually show how many instances belong to each point, we also show the histogram of the
distance (in the number of intervening sentences between the sentence containing the SF and the location) in Figure 2.

<figure>
  <div>
    <img src="/loc_stats_IL5_hist.png" width="45%"/>
    <img src="/loc_stats_IL6_hist.png" width="45%"/>
  </div>
  <div>
    <img src="/loc_stats_IL9_hist.png" width="45%"/>
    <img src="/loc_stats_IL10_hist.png" width="45%"/>
  </div>
  <p align="center">
    <strong>Figure 2.</strong>
    The histogram of distances (in the number of intervening sentences between the sentence containing the SF and the location) for
    the 4 ILs.
  </p>
</figure>

Here we can clearly see how most of the SF instances (70-90% of all SFs for which we can find the description) actually have their
location mention close to the sentence describing the SF itself. This might explain why the methods used by most teams to assign
location, which is based on proximity to the sentences found to be triggering the SF, work pretty well.
