import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import norm, poisson, nbinom
from matchups import MatchupInputs, project_matchup, market_probability, american_to_prob, fair_odds, expected_roi

st.set_page_config(page_title='Joseph AI Engine V2', page_icon='🏀', layout='wide')
st.title('Joseph AI Engine · V2')
st.caption('Player props • Matchup Intelligence • Market comparison | Independent, unvalidated prototype')
prop_tab, match_tab, board_tab = st.tabs(['🎯 Player Props', '🏟️ Matchups', '📋 Prop Board'])

with prop_tab:
    st.subheader('Player specialty analyzer')
    st.caption('Enter a player-specific projection. These are not live or trained model forecasts.')
    a,b,c = st.columns(3)
    with a:
        player=st.text_input('Player', 'Player A')
        market=st.selectbox('Specialty', ['Points','Rebounds','Assists','3-pointers','Receptions','Receiving yards','Passing yards','Rushing yards'])
        line=st.number_input('Prop threshold', min_value=0., value=24.5, step=.5)
    with b:
        odds=st.number_input('Over American odds', value=-110, step=5)
        mean=st.number_input('Baseline projected average', min_value=0., value=26., step=.5)
        sd=st.number_input('Projected standard deviation', min_value=.1, value=6., step=.5)
    with c:
        model=st.selectbox('Distribution', ['Normal','Poisson','Negative binomial'])
        matchup_pct=st.slider('Opponent matchup adjustment to mean (%)',-40,40,0)
        role_pct=st.slider('Minutes / opportunity adjustment (%)',-40,40,0)
    adjusted_mean=mean*(1+matchup_pct/100)*(1+role_pct/100)
    if model=='Normal':
        p=float(norm.sf(line, loc=adjusted_mean, scale=sd))
        samples=np.random.default_rng(42).normal(adjusted_mean,sd,10000)
    elif model=='Poisson':
        p=float(poisson.sf(int(np.floor(line)),mu=max(adjusted_mean,1e-9)))
        samples=np.random.default_rng(42).poisson(adjusted_mean,10000)
    else:
        variance=max(sd**2,adjusted_mean+0.001)
        r=max(adjusted_mean**2/(variance-adjusted_mean),1e-6)
        success=r/(r+adjusted_mean)
        p=float(nbinom.sf(int(np.floor(line)),r,success))
        samples=np.random.default_rng(42).negative_binomial(r,success,10000)
    if odds == 0:
        st.error('American odds cannot be zero.')
    else:
        q=american_to_prob(odds)
        m1,m2,m3,m4=st.columns(4)
        m1.metric('Estimated over',f'{p:.1%}')
        m2.metric('Break-even',f'{q:.1%}')
        m3.metric('Probability edge',f'{(p-q)*100:+.1f} pp')
        m4.metric('Estimated ROI',f'{expected_roi(p,odds):+.1%}')
        st.write(f'**{player} {market} over {line:g}** · adjusted mean {adjusted_mean:.2f} · illustrative fair odds {fair_odds(p)}')
        st.bar_chart(pd.DataFrame({'outcome':np.floor(samples).astype(int)}).groupby('outcome').size().rename('Simulated frequency'))
        st.caption('Matchup and role adjustments are YOUR scenario assumptions, not automatically estimated effects. The normal model is continuous; count markets are better tested with discrete models.')

with match_tab:
    st.subheader('Team matchup simulator')
    st.caption('Use season-adjusted team inputs from a trusted source. No games, injuries or odds are automatically fetched.')
    sport=st.radio('Sport', ['NBA','NFL'], horizontal=True, key='matchsport')
    nba=sport=='NBA'
    left,right=st.columns(2)
    with left:
        away=st.text_input('Away team','Away')
        away_o=st.number_input('Away offense — '+('points / 100 possessions' if nba else 'points / game'),min_value=0.,value=114. if nba else 23.,step=.5)
        away_d=st.number_input('Away defense — '+('points allowed / 100 possessions' if nba else 'points allowed / game'),min_value=0.,value=114. if nba else 22.,step=.5)
        away_p=st.number_input('Away pace — '+('possessions / 48 min' if nba else 'offensive plays / game'),min_value=1.,value=100. if nba else 63.,step=1.)
        away_adj=st.number_input('Away lineup/injury score adjustment (points)',value=0.,step=.5)
    with right:
        home=st.text_input('Home team','Home')
        home_o=st.number_input('Home offense — '+('points / 100 possessions' if nba else 'points / game'),min_value=0.,value=116. if nba else 24.,step=.5)
        home_d=st.number_input('Home defense — '+('points allowed / 100 possessions' if nba else 'points allowed / game'),min_value=0.,value=112. if nba else 21.,step=.5)
        home_p=st.number_input('Home pace — '+('possessions / 48 min' if nba else 'offensive plays / game'),min_value=1.,value=99. if nba else 62.,step=1.)
        home_adj=st.number_input('Home lineup/injury score adjustment (points)',value=0.,step=.5)
    with st.expander('Model assumptions and uncertainty',expanded=False):
        home_adv=st.number_input('Home court / field scoring advantage (points)',value=2.0 if nba else 1.5,step=.5)
        margin_sd=st.number_input('Game margin standard deviation',min_value=0.1,value=12.0 if nba else 13.5,step=.5)
        total_sd=st.number_input('Game total standard deviation',min_value=0.1,value=18.0 if nba else 13.0,step=.5)
    res=project_matchup(MatchupInputs(sport,away,home,away_o,away_d,home_o,home_d,away_p,home_p,home_adv,away_adj,home_adj,margin_sd,total_sd))
    st.markdown(f'### {away} @ {home}')
    a,b,c,d=st.columns(4)
    a.metric('Projected score',f'{res["away_points"]:.1f} – {res["home_points"]:.1f}')
    b.metric('Projected winner',home if res['home_win']>=.5 else away)
    c.metric(f'{home} win probability',f'{res["home_win"]:.1%}')
    d.metric('Projected game total',f'{res["total"]:.1f}')
    st.write(f'**Model spread:** {home} {(-res["home_margin"]):+.1f} (home margin {res["home_margin"]:+.1f}).')
    st.progress(res['home_win'],text=f'{home}: {res["home_win"]:.1%} · {away}: {res["away_win"]:.1%}')
    st.markdown('#### Compare with sportsbook markets')
    ca,cb=st.columns(2)
    with ca:
        home_ml=st.number_input(f'{home} moneyline odds',value=-110,step=5)
        spread=st.number_input(f'{home} spread (e.g. -3.5)',value=-3.5,step=.5)
        spread_odds=st.number_input(f'{home} spread odds',value=-110,step=5)
    with cb:
        total_line=st.number_input('Sportsbook total line',value=225.5 if nba else 45.5,step=.5)
        total_side=st.radio('Total selection',['Over','Under'],horizontal=True)
        total_odds=st.number_input('Total selection odds',value=-110,step=5)
    if 0 in (home_ml,spread_odds,total_odds):
        st.warning('American odds cannot equal zero.')
    else:
        spread_p=market_probability(res['home_margin'],margin_sd,-spread,'Over')
        total_p=market_probability(res['total'],total_sd,total_line,total_side)
        comparisons=pd.DataFrame([
            {'Market':f'{home} moneyline','Model probability':res['home_win'],'Odds':home_ml},
            {'Market':f'{home} {spread:+g}','Model probability':spread_p,'Odds':spread_odds},
            {'Market':f'{total_side} {total_line:g}','Model probability':total_p,'Odds':total_odds},
        ])
        comparisons['Break-even probability']=comparisons['Odds'].apply(american_to_prob)
        comparisons['Probability edge (pp)']=100*(comparisons['Model probability']-comparisons['Break-even probability'])
        comparisons['Estimated ROI']=comparisons.apply(lambda x:expected_roi(x['Model probability'],x['Odds']),axis=1)
        comparisons['Fair odds']=comparisons['Model probability'].apply(fair_odds)
        st.dataframe(comparisons.style.format({'Model probability':'{:.1%}','Break-even probability':'{:.1%}','Probability edge (pp)':'{:+.1f}','Estimated ROI':'{:+.1%}'}),hide_index=True,use_container_width=True)
        st.download_button('Export matchup analysis CSV',comparisons.to_csv(index=False),'joseph_matchup.csv','text/csv')
    st.info('Matchup probabilities assume normally distributed scoring margin/total and manually entered variance. NBA pace is used in projection; NFL pace is shown for context only. This is NOT a validated 85–90% model. Push outcomes are not separately modeled for whole-number spreads/totals.')

with board_tab:
    st.subheader('Multi-player prop comparison')
    st.caption('Normal-distribution approximation for manual scenario testing. Rows are examples, not live players.')
    initial=pd.DataFrame([{'Player':'Player A','Market':'Points','Line':24.5,'Odds':-110,'Mean':26.,'SD':6.,'Matchup adjustment %':0.},{'Player':'Player B','Market':'Rebounds','Line':7.5,'Odds':-125,'Mean':8.2,'SD':2.8,'Matchup adjustment %':0.}])
    df=st.data_editor(initial,num_rows='dynamic',hide_index=True,use_container_width=True)
    try:
        out=df.copy()
        for col in ['Line','Odds','Mean','SD','Matchup adjustment %']:out[col]=pd.to_numeric(out[col],errors='raise')
        if (out['SD']<=0).any() or (out['Mean']<0).any() or (out['Odds']==0).any():raise ValueError('SD must be positive, means nonnegative, and odds nonzero')
        adjusted=out['Mean']*(1+out['Matchup adjustment %']/100)
        if (adjusted<0).any():raise ValueError('Adjusted mean cannot be negative')
        out['Estimated probability']=norm.sf(out['Line'],loc=adjusted,scale=out['SD'])
        out['Break-even probability']=out['Odds'].apply(american_to_prob)
        out['Edge (pp)']=100*(out['Estimated probability']-out['Break-even probability'])
        out['Estimated ROI']=out.apply(lambda x:expected_roi(x['Estimated probability'],x['Odds']),axis=1)
        out=out.sort_values('Estimated ROI',ascending=False)
        st.dataframe(out.style.format({'Estimated probability':'{:.1%}','Break-even probability':'{:.1%}','Edge (pp)':'{:+.1f}','Estimated ROI':'{:+.1%}'}),hide_index=True,use_container_width=True)
        st.download_button('Export prop board CSV',out.to_csv(index=False),'joseph_prop_board.csv','text/csv')
    except (ValueError,TypeError) as e:st.warning(f'Please correct board inputs: {e}')

st.divider()
st.caption('Joseph AI V2 is an educational analytics prototype, not an AI trained on actual results. It has no direct Hard Rock integration, real-time data, automated betting or guaranteed win rates.')
