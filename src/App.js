import "./App.css";
import React, { Component } from "react";

const errors = [
  {
    code: 403,
    name: "Permission denied",
    domain: "wiki.uia.no",
    url: "wiki.uia.no/secret_uia_tech_cult",
    source: "wiki.uia.no",
    suggestion: "Check if the URL links to a non-public resource, or ask the owner for access if the URL is correct.",
  },
  {
    code: 404,
    name: "Site/resource was not found",
    domain: "www.uia.no",
    url: "www.uia.no/resources/how_to_cheat",
    source: "www.uia.no/resources",
    suggestion: "Ensure the URL is spelled correctly.  The resource may also have been deleted or removed, check with the owner.",
  },
  {
    code: 404,
    name: "Site/resource was not found",
    domain: "birdwatching.uia.no",
    url: "birdwatching.uia.no",
    source: none,
    suggestion: "Ensure the URL is spelled correctly.  The resource may also have been deleted or removed, check with the owner.",
  },
];

class App extends Component {
  state = {
    main_domain: "",
    should_find_domains: false,
    should_search: false,
    errors: errors,
  };
  find_domains = () => {
    if (!this.should_find_domains) {
      return;
    }
    //find domains to search
    console.log("find domains for: ", this.main_domain);
  };
  search_sites = () => {};

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <ul>
            {errors.map((v, i) => (
              <Error key={i} props={v} />
            ))}
          </ul>
        </header>
      </div>
    );
  }
}

class Error extends Component {
  state = { error_code: 404, error_title: "", url_domain: "", full_url: "" };
  constructor(props) {
    super(props);
    this.state = props.props;
  }
  render() {
    return (
      <li style={{ textAlign: "left" }}>
        {this.state.error_code},{this.state.full_url}
      </li>
    );
  }
}
export default App;
