import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Display all characters in each column
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', None)

# Import the data
df = pd.read_csv("C:/MS_project/doc_grid.csv")
df.head()

# FIx the incorrectly labelled file path for 14win std3 replicate 1
df['File Path'] = df['File Path'].replace(r'D:\Stellena\Data_May 2023_timsTOF_Lipid Analysis_DIA PASEF\20230508_DIA_windowtest\UltimateSplash_Var_PIP_14win_std3_6_1_16383.d', 
                                          r'D:\Stellena\Data_May 2023_timsTOF_Lipid Analysis_DIA PASEF\20230508_DIA_windowtest\UltimateSplash_Var_PIP_14win_std3_6_3_16383.d')



# Count the number of unique values in a column
df['Molecule'].nunique()
# Remove rows where the value in the Molecule column is NaN
df = df.dropna(subset=['Molecule'])

# Extract everything after 'UltimateSplash_'
df['After_UltimateSplash'] = df['File Path'].str.split('UltimateSplash_').str[1]
df['After_UltimateSplash']

# Add another column called window_type
# If the value in the After_UltimateSplash column begins with a number, then the window_type is "fixed"
# If the value in the After_UltimateSplash column begins with "Var", then the window_type is "variable"
# If the value in the After_UltimateSplash column begins with "NW", then the window_type is "none"
df['window_type'] = df['After_UltimateSplash'].apply(lambda x: 'fixed' if x[0].isdigit() else 'variable' if x[0:3] == 'Var' else 'none')

# Remove Var_PIP_ from the After_UltimateSplash column
df['After_UltimateSplash'] = df['After_UltimateSplash'].str.replace('Var_PIP_', '')

# Extract elements separated by '_'
df[['Window', 'Dilution', 'Replicate']] = df['After_UltimateSplash'].str.split('_', expand=True).iloc[:, [0,1,3]]
df['Window'].value_counts()
df['Dilution'].value_counts()
# Select only rows in df where there is no "+Na" in the Precursor Adduct column
df = df[~df['Precursor Adduct'].str.contains('\+Na')]

# If the value in the column "Total Background MS1" is 0, then replace it with 1
df['Total Background MS1'] = df['Total Background MS1'].replace(0, 1)
# See how many values in the "Total Area MS1" column are NaN or 0
df['Total Area MS1'].isna().sum() + (df['Total Area MS1'] == 0).sum()

# Number of rows in df
len(df)
df[(df['Window'] == '14win') & (df['Molecule'] == '14:0-13:0-14:0 TG-d5') & (df['Dilution'] == 'std3')]

# Import transitions
transitions = pd.read_csv('C:/MS_project/UltimateSplash_Pos_v2.csv')

# Subset transition_subset for columns "PrecursorAdduct", "ProductName", "ProductMz"
transitions = transitions[['PrecursorName', 'PrecursorAdduct', 'ProductName', 'ProductMz']]
# Remove "1+" from the values in the "PrecursorAdduct" column
transitions['PrecursorAdduct'] = transitions['PrecursorAdduct'].str.replace('1+', '')
# Remove rows where the value in the "ProductMz" column is NaN
transitions = transitions.dropna(subset=['ProductMz'])

# Left merge transitions with df on columns "PrecursorName" and "PrecursorAdduct" and "ProductMz"
df = df.merge(transitions, how='left', left_on = ["Molecule", "Precursor Adduct", "Chromatogram Product M/Z"], right_on = ["PrecursorName", "PrecursorAdduct", "ProductMz"])

# Add a column in df called "Precursor", which contains True and False values. True if the value in ProductName is precursor, False if not
df['not_precursor'] = df['ProductName'].str.contains('precursor')
df['not_precursor'] = df['not_precursor'].fillna(False).astype(bool)
df['not_precursor'] = ~df['not_precursor']
len(df)

df.tail(20)


# Check if there are lipid adducts with the same window, dilution, replicate, but different total area MS1
# These are all 14win, std3, replicate 1
df_nodup = df.drop_duplicates(subset=['Molecule', 'Window', 'Dilution', 'Replicate', 'Total Area MS1'])
df_nodup[df_nodup.duplicated(subset=['Molecule', 'Window', 'Dilution', 'Replicate'], keep=False)]

df_nodup[(df_nodup['Replicate'] == '3') & (df_nodup['Dilution'] == 'std3') & (df_nodup['Window'] == '28win')]

# Subset for only product ion transitions
df_MS2_only  = df[df['not_precursor']]
df_subset = df_MS2_only[['Molecule', 'Molecule List', 'window_type', 'Window', 'Dilution', 'Replicate', 'Background', 'Area', 'Total Area MS1', 'Total Background MS1', 'not_precursor']]

# Group by 'Molecule', 'Window', and 'Replicate', sum the "Area" column for rows where is_precursor == 'False' and then
# Add a new column to the df_subset dataframe called "Total Area MS2" which contains the sum of the "Area" column corresponding to each Molecule, Window and replicate
df_subset['Total Area MS2'] = df_subset.groupby(['Molecule', 'Window', 'Dilution', 'Replicate'])['Area'].transform('sum')
df_subset['Total Background MS2'] = df_subset.groupby(['Molecule', 'Window', 'Dilution', 'Replicate'])['Background'].transform('sum')
# If the value in the 'Total Background MS2' column is 0, then replace it with 1
df_subset['Total Background MS2'] = df_subset['Total Background MS2'].replace(0, 1)

df_subset[(df_subset['Molecule'] == '14:0-13:0-14:0 TG-d5') & (df_subset['Dilution'] == 'std3') & (df_subset['Window'] == '14win') & (df_subset['Replicate'] == '1')]

# Remove rows in df_subset where the value in the "Total Area MS1" is duplicate
# The subset parameter is used to specify the columns that should be considered when identifying duplicates.
# Some lipid adducts with the same window, dilution, replicate, have different total area MS1
# df_subset = df_subset.drop_duplicates(subset=['Molecule', 'Molecule List', 'window_type', 'Window', 'Dilution', 'Replicate', 'Total Area MS1', 'Total Area MS2', 'Total Background MS1', 'Total Background MS2'])
df_subset = df_subset.drop_duplicates(subset=['Molecule', 'window_type', 'Window', 'Dilution', 'Replicate'])

# Remove columns Background and Area
df_subset = df_subset.drop(columns=['Background', 'Area'])
# Add column to df_subset called SN_MS1 and SN_MS2
df_subset['SN_MS1'] = df_subset['Total Area MS1'] / df_subset['Total Background MS1']
df_subset['SN_MS2'] = df_subset['Total Area MS2'] / df_subset['Total Background MS2']

# Fixed window
# df_subset = df_subset[(df_subset['Dilution'] == 'std1') & ((df_subset['window_type'] == 'fixed') | (df_subset['window_type'] == 'none'))]
# order = ['NW', '200da', '100da', '50da', '25da']
# Variable window
df_subset = df_subset[(df_subset['Dilution'] == 'std3') & ((df_subset['window_type'] == 'variable') | (df_subset['window_type'] == 'none'))]
order = ['NW', '4win', '7win', '14win', '28win']

# Convert the 'Window' column to a category and specify the order
df_subset['Window'] = pd.Categorical(df_subset['Window'], categories=order, ordered=True)
df_subset = df_subset.sort_values('Window')
df_subset['Window'].value_counts()

win14_df = df_subset[(df_subset['Window'] == '14win') & (df_subset['Dilution'] == 'std3')]
df_subset[(df_subset['Window'] == '14win') & (df_subset['Dilution'] == 'std3') & (df_subset['Molecule'] == '14:0-13:0-14:0 TG-d5')]
# Plot histogram of Total Area MS2 for win14_df
win14_df['Total Area MS2'].hist(bins=100)
plt.title('Histogram of Total Area MS2 for 14win')
plt.xlabel('Total Area MS2')
plt.ylabel('Frequency')
plt.show()

# Plot histogram of Total Area MS1 for win14_df
win14_df['Total Area MS1'].hist(bins=100)
plt.title('Histogram of Total Area MS1 for 14win')
plt.xlabel('Total Area MS1')
plt.ylabel('Frequency')
plt.show()

# Subset rows in win14_df where the value in the "Total Area MS2" column is greater than 2 * 1e7
win14_df[win14_df['Total Area MS2'] > 2 * 1e7]

# Define a function to calculate the coefficient of variation
def calculate_cv(x):
    return (x.std() / x.mean()) * 100

# Group by 'Molecule' and 'Window', then calculate the CV for each group
# Rename the 'Total Ion Current Area' column to 'CV'
cv_df = df_subset.groupby(['Window', 'Molecule'])['Total Area MS1'].apply(calculate_cv).reset_index()
cv_df.rename(columns={'Total Area MS1': 'CV_MS1'}, inplace=True)
cv_temp = df_subset.groupby(['Window', 'Molecule'])['Total Area MS2'].apply(calculate_cv).reset_index()
cv_temp.rename(columns={'Total Area MS2': 'CV_MS2'}, inplace=True)
cv_temp[(cv_temp['Window'] == '14win')]
len(cv_temp[(cv_temp['Window'] == '14win')])

# Merge cv_df with cv_temp on 'Molecule' and 'Window'
cv_df = cv_df.merge(cv_temp, on=['Molecule', 'Window'])
cv_df[(cv_df['Window'] == '14win')]

# Merge cv_df with df_subset on 'Molecule' and 'Window'
# cv_df = cv_df.merge(df_subset, on=['Molecule', 'Window', 'Replicate'])
# Subset cv_df for rows where the Molecule list is not PE
# cv_df_no_PE = cv_df[cv_df['Molecule List'] != 'PE']
cv_df

# Make boxplot of CV from cv_df by 'Window' 
# cv_df.boxplot(column='CV', by='Window', showfliers=False)
# plt.suptitle('')
# plt.title('Coefficient of Variation (CV) (%) of Area for Lipid Adducts MS1 std3')
# plt.xlabel('Window')
# plt.ylabel('CV')
# plt.show()



# Reshape the DataFrame from wide format to long format
long_df = cv_df.melt(id_vars='Window', value_vars=['CV_MS1', 'CV_MS2'], var_name='CV_Type', value_name='CV')

long_df[long_df['Window'] == '14win']

# Create the boxplot
sns.boxplot(x='Window', y='CV', hue='CV_Type', data=long_df, palette=['#B56962', '#64A07E'], showfliers=False)
# Show outliers


plt.title('Coefficient of Variation (CV) (%) of Area for Lipid Adducts std3')
plt.xlabel('Window')
plt.ylabel('CV')
plt.show()



# Create an empty dataframe and add a column to it
# Run each row individually
cv_sum_df = pd.DataFrame()
cv_sum_df['std1'] = cv_df['CV']
cv_sum_df['std2'] = cv_df['CV']
cv_sum_df['std3'] = cv_df['CV']



# Merge cv_sum_df with cv_df on 'std3' and 'CV'
# Rename the 'CV' column to 'std3' in cv_df
cv_df.rename(columns={'CV': 'std3'}, inplace=True)
cv_sum_df = cv_sum_df.merge(cv_df, on=['std3'])

# Save and load the dataframe
# cv_sum_df.to_csv('cv_all_stds_var_win.csv', index=False)
cv_sum_df = pd.read_csv('cv_all_stds_fixed_win.csv')
order = ['NW', '200da', '100da', '50da', '25da']
cv_sum_df['Window'] = pd.Categorical(cv_sum_df['Window'], categories=order, ordered=True)
cv_sum_df = cv_sum_df.sort_values('Window')

# Change cv_sum_df to long format
cv_sum_long = cv_sum_df.melt(id_vars=['Window', 'Molecule'], value_vars=['std1', 'std2', 'std3'], var_name='Dilution', value_name='CV')
# Make box plot of CV from cv_sum_long by 'Window'
cv_sum_long.boxplot(column='CV', by='Window', showfliers=False)
plt.suptitle('')
plt.title('Coefficient of Variation (CV) (%) of Area for Lipid Adducts MS1 (all dilutions)')
plt.xlabel('Window')
plt.ylabel('CV')
plt.show()


