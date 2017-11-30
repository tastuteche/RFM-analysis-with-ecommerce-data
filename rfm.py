import pandas as pd
from datetime import datetime
import seaborn as sns
from tastu_teche.plt_show import plt_show, df_show, set_show, plt_figure, ax_hbar_value, ax_vbar_value
sns.set()

transaction_data = pd.read_csv('transaction_data_clean.csv', dtype={
                               'CustomerID': str, 'InvoiceNO': str})
t = transaction_data
t[t.Description == '85123A']['StockCode'].value_counts()
t[t.Description == 'WHITE HANGING HEART T-LIGHT HOLDER']['StockCode'].value_counts()

t['InvoiceDate'] = pd.to_datetime(t['InvoiceDate'])


# We create two classes for the RFM segmentation since, being high recency is bad, while high frequency and monetary value is good.
# Arguments (x = value, p = recency, monetary_value, frequency, k = quartiles dict)
def RClass(x, p, d):
    if x <= d[p][0.25]:
        return 1
    elif x <= d[p][0.50]:
        return 2
    elif x <= d[p][0.75]:
        return 3
    else:
        return 4

# Arguments (x = value, p = recency, monetary_value, frequency, k = quartiles dict)


def FMClass(x, p, d):
    if x <= d[p][0.25]:
        return 4
    elif x <= d[p][0.50]:
        return 3
    elif x <= d[p][0.75]:
        return 2
    else:
        return 1


def rfm(orders, inputdate):
    NOW = datetime.strptime(inputdate, "%Y-%m-%d")

    rfmTable = orders.groupby('CustomerID').agg({'InvoiceDate': lambda x: (NOW - x.max()).days,  # Recency
                                                 # Frequency
                                                 'InvoiceNo': lambda x: len(x),
                                                 'monetary_value': lambda x: x.sum()})  # Monetary Value

    rfmTable['InvoiceDate'] = rfmTable['InvoiceDate'].astype(int)
    rfmTable.rename(columns={'InvoiceDate': 'recency',
                             'InvoiceNo': 'frequency',
                             'monetary_value': 'monetary_value'}, inplace=True)

    quantiles = rfmTable.quantile(q=[0.25, 0.5, 0.75])
    quantiles = quantiles.to_dict()

    rfmSegmentation = rfmTable

    rfmSegmentation['R_Quartile'] = rfmSegmentation['recency'].apply(
        RClass, args=('recency', quantiles,))
    rfmSegmentation['F_Quartile'] = rfmSegmentation['frequency'].apply(
        FMClass, args=('frequency', quantiles,))
    rfmSegmentation['M_Quartile'] = rfmSegmentation['monetary_value'].apply(
        FMClass, args=('monetary_value', quantiles,))

    rfmSegmentation['RFMClass'] = rfmSegmentation.R_Quartile.map(
        str) + rfmSegmentation.F_Quartile.map(str) + rfmSegmentation.M_Quartile.map(str)

    return rfmSegmentation


t['InvoiceDate'].max()
NOW = '2011-12-12'


def get_segment_rank_title(code):
    if code == '111':
        return 0, 'Best Customers'
    if code[1] == '1':
        return 1, 'Loyal Customers'
    if code[2] == '1':
        return 2, 'Big Spenders'
    if code[0] == '1':
        return 3, 'Recent Customers'
    if code == '311':
        return 4, 'Almost Lost'
    if code == '411':
        return 5, 'Lost Customers'
    if code == '444':
        return 6, 'Lost Cheap Customers'
    return 7, 'Others'


rfmSegmentation = rfm(t, NOW)

rfmSegmentation['segment_title'] = rfmSegmentation.RFMClass.map(
    lambda x: get_segment_rank_title(x)[1])
rfmSegmentation['segment_rank'] = rfmSegmentation.RFMClass.map(
    lambda x: get_segment_rank_title(x)[0])

rfm_count = rfmSegmentation.groupby(['segment_title', 'segment_rank']).size(
).reset_index().sort_values('segment_rank')
rfm_count.columns = ['segment_title', 'segment_rank', 'count']
rfm_count_rpt = rfm_count[['segment_title', 'count']]

df_show(rfm_count_rpt, 'rfm_count_rpt.txt', '# of Customers / Segment')

rfm_recency = rfmSegmentation.groupby(
    ['segment_title', 'segment_rank'])['recency'].mean().reset_index().sort_values('segment_rank')
rfm_recency.columns = ['segment_title', 'segment_rank', 'recency']
rfm_recency_rpt = rfm_recency[['segment_title', 'recency']]
plt_figure(10)
ax = sns.barplot(y="segment_title", x="recency", data=rfm_recency_rpt)
ax_hbar_value(ax)
plt_show('average_recency.png')

rfmSegmentation['frequency']
rfm_order_count = rfmSegmentation['frequency'].value_counts(
).sort_index().reset_index()
rfm_order_count.columns = ['frequency', 'customer_count']

plt_figure(15)
ax = sns.barplot(x="frequency", y="customer_count",
                 data=rfm_order_count.head(50))
ax_vbar_value(ax)
plt_show('customer_vs_order.png')

R_F = pd.pivot_table(rfmSegmentation, index='R_Quartile',
                     columns='F_Quartile', values='segment_rank', aggfunc=len, fill_value=0)
R_F_rpt = R_F.applymap(lambda x: x / R_F.values.sum())
ax = sns.heatmap(R_F_rpt, annot=True, fmt=".2%", linewidths=.5)
ax.set_title('Recency x Frequency(% of Customers)')
plt_show('recency_vs_frequency.png')

rfm_rpt = rfmSegmentation.reset_index()[['CustomerID',
                                         'segment_title', 'RFMClass', 'recency', 'frequency', 'monetary_value']]

C = rfm_rpt.style.format({'monetary_value': '${0:.2f}'})
rfm_rpt['monetary_value'] = rfm_rpt['monetary_value'].map('${:,.2f}'.format)
df_show(rfm_rpt.head(10), 'rfm_rpt.txt', '# of Customers / Segment / RFM')
