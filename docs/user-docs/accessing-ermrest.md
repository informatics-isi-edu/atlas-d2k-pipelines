# Accessing ERMrest

In this document, we will go through some examples of accessing ERMrest. For more information, please refer to ERMrest docs:
- Main page: https://docs.derivacloud.org/ermrest/api-doc/index.html
- Data Operations (https://docs.derivacloud.org/ermrest/api-doc/data/rest.html):
  - Entity Retrieval (https://docs.derivacloud.org/ermrest/api-doc/data/rest.html#entity-retrieval)
  - Attribute Retrieval (https://docs.derivacloud.org/ermrest/api-doc/data/rest.html#attribute-retrieval)
  - Attribute Group Retrieval (https://docs.derivacloud.org/ermrest/api-doc/data/rest.html#attribute-group-retrieval)



## HRA 3D Coordinate and Specimen


The Specimen records are stored under `Gene_Expression:Specimen` table. The following is a simple
`entity` request to fetch the first 25 rows:

```
https://www.atlas-d2k.org/ermrest/catalog/2/entity/Gene_Expression:Specimen@sort(RID)?limit=25
```

You can use the `attribute` API to limit the projected columns:

```
https://www.atlas-d2k.org/ermrest/catalog/2/attribute/Gene_Expression:Specimen/RID,Parent_Specimen,HRA_3D_Coordinate@sort(RID)?limit=25
```

And if you want to see the records that have HRA 3D Coordinate:

```
https://www.atlas-d2k.org/ermrest/catalog/2/entity/Gene_Expression:Specimen/!(HRA_3D_Coordinate::null::)@sort(RID)?limit=25

https://www.atlas-d2k.org/ermrest/catalog/2/attribute/Gene_Expression:Specimen/!(HRA_3D_Coordinate::null::)/RID,Parent_Specimen,HRA_3D_Coordinate@sort(RID)?limit=25
```




Removing `?limit=25` will return all the rows in the database. We highly recommend against doing this as it could slow down
the whole server. Instead, we recommend getting the data page by page and appending them together if you need to. The following
is a simple example of doing this with JavaScript:


```ts
/**
 * a simple GET request to demonstrate how you can use pagination to grab all the data in muliple requests.
 *
 * Assume we have n rows, and due to performance concerns, we want to limit the request to only pageLimit rows.
 * This function will first ask for pageLimit+1 results. If we get less than the requested number of rows, we're done.
 * But if we recieve pageLimit+1 records, there might be more. So we're going to ask for the next page of results.
 *
 * Notes:
 * - In ermrest the sort and page criteria must be referring to the same columns. In this simple example
 *   we're always sorting values by the RID column. so you have to make sure RID is one of the projected columns.
 *   feel free to adjust this for other cases.
 * - In this example I'm using fetch which will not use any cookies. So it will only fetch publicly available data.
 *   If you want to get all the available data, you need to find the cookie of a user with proper access and use
 *   that for this request. In our internal test framework, we do this by manually setting the `webauthn` cookie.
 *
 * @param {string} url
 * @param {number} pageLimit
 * @param {string?} afterRIDValue
 * @returns
 */
const fetchAllRows = async (url, pageLimit, afterRIDValue) => {
  try {
    let usedURL = url + '@sort(RID)';
    if (afterRIDValue) {
      usedURL += `@after(${afterRIDValue})`;
    }
    // ask for one more row
    usedURL += '?limit=' + (pageLimit + 1);
    console.log(`sending GET request to: ${usedURL}`);

    const response = await fetch(usedURL);

    if (response.status !== 200) {
      console.error('did not recieve a 200 response');
      console.log(await response.text());
      return [];
    }

    let responseRows = await response.json();
    if (responseRows.length > pageLimit) {
      // remove the extra item that we recieved
      responseRows.pop();
      const lastRowRID = responseRows[responseRows.length - 1].RID;

      // go for the next page
      const nextRows = await fetchAllRows(url, pageLimit, lastRowRID);
      // append the current page of results with the other ones.
      return responseRows.concat(nextRows);
    } else {
      return responseRows;
    }
  } catch (err) {
    console.error('error while fetching data');
    console.error(err);
  }
};


const getSpecimen = async () => {
  // limit the projected columns
  const specimenAttribute = 'https://www.atlas-d2k.org/ermrest/catalog/2/attribute/Gene_Expression:Specimen/RID,Parent_Specimen,HRA_3D_Coordinate';
  // limit the result to only rows with HRA_3D_Coordinate
  // const specimenAttribute = 'https://www.atlas-d2k.org/ermrest/catalog/2/attribute/Gene_Expression:Specimen/!(HRA_3D_Coordinate::null::)/RID,Parent_Specimen,HRA_3D_Coordinate';
  // use the simple entity API
  // const specimenEntity = 'https://www.atlas-d2k.org/ermrest/catalog/2/entity/Gene_Expression:Specimen';
  // if you want to filter to only human
  // const specimenEntity = 'https://www.atlas-d2k.org/ermrest/catalog/2/entity/Gene_Expression:Specimen/Species=Homo%20sapiens';

  // we're fetching 500 records at a time. feel free to adjust it based on the performance
  const rows = await fetchAllRows(specimenAttribute, 3000);
  console.log(`count: ${rows.length}`);
  // console.log(rows);
}

getSpecimen();
```




The HRA 3D Coordinate data is stored under `Gene_Expression:HRA_3D_Coordinate` table. The following is an example of fetching the data (using the same `fetchAllRows` as above):


```ts
const getCoordinates = async () => {
  // use the simple entity API
  const HRACoordinates = 'https://www.atlas-d2k.org/ermrest/catalog/2/entity/Gene_Expression:HRA_3D_Coordinate/';
  // use the attribute API to limit the projected columns
  // const HRACoordinates = 'https://www.atlas-d2k.org/ermrest/catalog/2/attribute/Gene_Expression:HRA_3D_Coordinate/RID,File_URL';

  /**
   * we're storing the registry file URL in this column. in the following we're showing example of fetching the file.
   */
  const REGISTRY_FILE_URL_COLUMN = 'File_URL';

  const rows = await fetchAllRows(HRACoordinates, 500);

  // go through each row and fetch the registry files.
  for await (const row of rows) {
    console.log(`row with RID=${row.RID}`);
    console.log(row);

    const registryFileURL = row[REGISTRY_FILE_URL_COLUMN];
    if (registryFileURL) {
      const response = await fetch(`https://www.atlas-d2k.org${registryFileURL}`);
      if (response.status === 200) {
        const registry = await response.json();
        console.log(`registry file:`);
        console.log(registry);
      }
    }

    console.log('============================\n');
  }
}

getCoordinates();
```
