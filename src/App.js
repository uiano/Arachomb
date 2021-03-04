import "./App.css";
import React, { Component } from "react";

const errors = [
  {
    error_code: 300,
    error_title: "something went wrong",
    url_domain: "wiki.uia.no",
    full_url: "wiki.uia.no/secret_uia_tech_cult",
  },
  {
    error_code: 404,
    error_title: "something was missing",
    url_domain: "uia.no",
    full_url: "uia.no/how_to_cheat",
  },
  {
    error_code: 404,
    error_title: "something was missing",
    url_domain: "birdwatching.uia.no",
    full_url: "birdwatching.uia.no",
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
